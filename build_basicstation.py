import os
import shlex
import subprocess

from pyinfra import facts, host
from pyinfra.operations import apt, files, git, python, server

checkout_dir = "/usr/local/src/basicstation"

apt.update()
apt.packages(
    name="Install dependencies",
    packages=["build-essential", "gcc-riscv64-linux-gnu", "gcc-arm-linux-gnueabihf", "git"],
)

git.repo(
    name="Clone repo",
    src="https://github.com/lorabasics/basicstation",
    dest=checkout_dir,
)

# Usually platform=rpi is used for SX1301-based designs, but that is
# really not different from platform=linux except for the default ARCH.
# Since we're overriding that anyway, just use linux for the SX1301
# builds
output_files = []
for (platform, buildname) in (("corecell", "sx1302"), ("linux", "sx1301")):
    for (compiler, arch) in (("riscv64-linux-gnu", "riscv64"), ("arm-linux-gnueabihf", "armhf")):
        build_dir = f"build-{buildname}-{arch}"
        # The makefile uses TOOLCHAIN/bin/ARCH-gcc to find the compiler.
        # If we specify both, we can override the autodetected defaults.
        toolchain = "/usr"
        variant = "std"

        server.shell(
            name=f"Build basicstation for {buildname} on {arch}",
            # This cleans first, since most of the code is built inside
            # the build_dir, some deps (libloragw in particular) just
            # builds inside the source dir. There are different source
            # dirs for different platforms, but not for different archs,
            # so just clean, we'll need a full rebuild anyway.
            commands=[shlex.join([
                "make", "clean", "all", "-C", f"{checkout_dir}",
                f"platform={platform}",
                f"ARCH={compiler}",
                f"TOOLCHAIN={toolchain}",
                f"variant={variant}",
                f"BD={build_dir}",
            ])]
        )

        output_file = f"files/basicstation/{arch}-{buildname}/station"
        files.get(
            name=f"Extract basicstation binaries for {buildname} on {arch}",
            src=f"{checkout_dir}/{build_dir}/bin/station",
            dest=output_file,
            create_local_dir=True,
        )
        output_files.append(output_file)


def commit_result():
    parent = os.path.dirname(checkout_dir)
    base = os.path.basename(checkout_dir)
    cmd = (
        f"cd '{parent}';" +
        f"find '{base}' -name .git -printf '  %h: ' -exec git --git-dir {{}} describe --tags --always --long \\;"
    )
    versions = host.get_fact(facts.server.Command, cmd)
    message = "\n".join((
        "basicstation: Update binaries",
        "",
        f"This is the result of rebuilding the binaries using the {os.path.basename(__file__)}",
        "script. This uses the following source code versions:",
        "",
        versions,
    ))

    subprocess.run(['git', 'commit', '--message', message, *output_files], check=True)


python.call(
    name="Commit result",
    function=commit_result,
)
