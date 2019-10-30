import random
from uuid import uuid4
from robottelo.config import settings


class ContainerError(Exception):
    """Exception raised for failed container management operations."""


class DockerContainer:
    """
    Gather information needed to spin up a Docker-based container.
    Attributes:
            image (init): The name of the container image to build from.
            tag (init): The tag of the operating system to use.
            agent (boolian): If set to True, prepares container for
            katello-agent.
    """

    def __init__(self, image, tag, agent, ports):
        """
        Parameters:
            image (init): The name of the container image to build from.
            tag (init): The tag of the operating system to use.
            agent (boolian): If set to True, prepares container for
            katello-agent.
        Returns:
            A container object if tag and image supplied.
        """
        import docker
        import docker.api.container

        self._client = docker.Client(version="1.22")
        self.image = image
        self.tag = tag
        self.name = uuid4()
        self.ports = ports or {}
        self._inst = None
        self._logs = {}
        self._mount = agent
        self._create()

    def _create(self):
        """Creates containers for an instance of this class.
        Mounts /dev/log as a read-write file system if katello-agent
        is required.
        Prints RHSM logs to stout.
        Prints host name to stout after starting the container.
        """
        print(f"Creating {self.tag} container named {self.name}")
        volumes = (
            {"/dev/log": {"bind": "/dev/log", "mode": "rw"}} if self._mount
            else {}
        )
        self._inst = self._client.create_container(
            detach=False,
            host_config=self._client.create_host_config(
                binds=volumes, port_bindings=self.ports
            ),
            image=f"{self.image}:{self.tag}",
            ports=list(self.ports.keys()),
            command="tail -f /var/log/rhsm/rhsm.log",
        )
        self._client.start(container=self._inst)
        self.name = self.execute("hostname").strip()

    def delete(self):
        """Deletes all the containers belonging to an instance of this
        class."""
        print(f"Deleting {self.name}")
        self._client.remove_container(self._inst, v=True, force=True)

    def execute(self, command):
        """Executes a shell command.
        Parameters:
            command (init): A command to pass to the shell (CLI).
        """
        exec_inst = self._client.exec_create(
            container=self._inst, cmd=command, stdout=True
        )
        print(f"{self.name} is executing: {command}")
        return self._client.exec_start(exec_id=exec_inst).decode()

    def logs(self, file="stdout", tailing=False):
        """Enables logging to a file. Defaults to writing to stdout.
        Parameters:
            file (str): A file name to write to.
            tailing (boolian): If set to True, tails the log file.
        """
        if file == "stdout":
            current = self._client.logs(self._inst["Id"])
        else:
            current = self.execute(f"cat {file}")
        if isinstance(current, bytes):
            current = current.decode()
        self._logs[file] = current
        return current.replace(
            self._logs.get(file, ""), "") if tailing else current

    def port(self):
        """The port to use for SSH."""
        return self._client.port(self._inst["Id"], 22)[0]["HostPort"]


class Container:
    """Generic class to gather information for a Linux Container.
    It enables separating generic and runtime specific code.
    Calls a runtime specific class to build the container. Defaults to docker.
    Attributes:
        runtime (init): The Linux container runtime to use. Defaults to docker.
        image (init): The name of the container image to build from.
        tag (init): The tag of the operating system to use.
        agent (boolian): If set to True, prepares container for katello-agent.
        port (init): The port to use for SSH.
    Returns:
        A container object
    """

    def __init__(
            self, runtime="docker", image="ch-d", tag="rhel7", agent=False,
            ports=None
    ):
        if runtime == "docker":
            ContainerClass = DockerContainer
        # elif runtime == "podman":
        #     ContainerClass = PodmanContainer
        else:
            print("Invalid runtime selection")
        self._inst = ContainerClass(image=image, tag=tag, agent=agent,
                                    ports=ports)
        self._logs = self._inst._logs

    @property
    def name(self):
        return self._inst.name

    def delete(self):
        return self._inst.delete()

    def execute(self, command):
        return self._inst.execute(command)

    def logs(self, file="stdout", tailing=False):
        return self._inst.logs(file, tailing)

    def port(self):
        return self._inst.port()

    def register(
            self,
            host=settings.server.hostname,
            ak=None,
            org="Default_Organization",
            env="Library",
            auth=("admin", "changeme"),
            force=False,
    ):
        self._host = host
        res = self._inst.execute(
            f"curl --insecure --output katello-ca-consumer-latest.noarch.rpm \
                https://{host}/pub/katello-ca-consumer-latest.noarch.rpm"
        )
        res += self._inst.execute(
            "yum -y localinstall katello-ca-consumer-latest.noarch.rpm"
        )
        if "Complete!" not in res:
            print("Unable to install bootstrap rpm")
            return res
        reg_command = f'subscription-manager register --org="{org}"'
        if force:
            reg_command += " --force"
        if ak:
            res += self._inst.execute(f'{reg_command} --activationkey="{ak}"')
        else:
            res += self._inst.execute(
                f'{reg_command} --user="{auth[0]}" --password="{auth[1]}" \
                --environment="{env}"'
            )
        if "The system has been registered" not in res:
            raise ContainerError('Unable to register to system' +
                                 '/n output from container:' + res)
        return res

    def rex_setup(self, host=None):
        self._inst.execute("mkdir /root/.ssh")
        return self._inst.execute(
            f"curl -ko /root/.ssh/authorized_keys \
                https://{host or self._host}:9090/ssh/pubkey"
        )

    def install_katello_agent(self):
        """Installs katello agent on the Container.
        :return: result of stdout of installation katello-agent and goferd
        process check.
        :raises ContainerError: If katello-ca wasn't installed.
        """
        result = self._inst.execute("yum install -y katello-agent")

        result += self._inst.execute('rpm -q katello-agent')
        if "Complete!" not in result:
            raise ContainerError('Failed to install katello-agent')
        if not self._inst._mount:
            raise ContainerError('katello-agent is not running')
        return result


class ContainerContext:
    """A context manager for managing containers.
    Attributes:
        runtime (init): The Linux container runtime to use. Defaults to docker.
        image (init): The name of the container image to build from.
        tag (init): The tag of the operating system to use.
        count (init): The number to containers to build. Defaults to one.
        agent (boolian): If set to True, prepares container for katello-agent.
    Returns:
        A container object, if count == 1 and there is one tag.
        A list of container objects, if count > 1 and there is one tag.
        A dict with tags as keys and the above as values.
    """

    def __init__(
            self, runtime="docker", image="ch-d", tag="rhel7", count=1, agent=False
    ):
        if isinstance(tag, list):
            self.container = {}
            for _tag in tag:
                self.container[_tag] = [
                    Container(runtime, image, _tag, agent)
                    for _ in range(count)
                ]
                if len(self.container[_tag]) == 1:
                    self.container[_tag] = self.container[_tag][0]
        else:
            self.container = [
                Container(runtime, image, tag, agent) for _ in range(count)
            ]

    def __enter__(self):
        return self.container if len(self.container) > 1 else self.container[0]

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if isinstance(self.container, dict):
            for container in self.container.values():
                container.delete()
        else:
            for container in self.container:
                container.delete()
