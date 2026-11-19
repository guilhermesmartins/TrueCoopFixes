"""Build NVCoop.dll (True Co-op Fixes, based on New Vegas Co-op by Zyrcxies) on Linux without CMake/Visual Studio:
clang (MSVC/clang-cl mode) + lld-link against the MSVC CRT and Windows SDK downloaded by cargo-xwin. Mirrors
CMakeLists.txt (enet + nvcoop_core + NVCoop, Release, static CRT). FAKEFRIEND=1 builds tools/fakefriend instead.

  python3 tools/linux-build/build.py <out dir>        (XWIN = folder with crt/ and sdk/, default ~/Projects/toolchains/xwin-x86/xwin)
"""
import concurrent.futures as cf
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent
OUT = Path(sys.argv[1]).resolve()
X = Path(os.environ.get("XWIN", Path.home() / "Projects/toolchains/xwin-x86/xwin"))
OBJ = OUT / "obj"
OBJ.mkdir(parents=True, exist_ok=True)
CLANG = os.environ.get("CLANG", "clang-18")
cm = (SRC / "CMakeLists.txt").read_text()


def target_sources(name):
    m = re.search(rf"add_library\({name}\s+(?:STATIC|SHARED)?\s*(.*?)\)", cm, re.S)
    return [s for s in m.group(1).split() if s.endswith((".c", ".cpp"))]


SYS = ["-imsvc", str(X / "crt/include"), "-imsvc", str(X / "sdk/include/ucrt"), "-imsvc", str(X / "sdk/include/um"),
       "-imsvc", str(X / "sdk/include/shared")]
BASE = [CLANG, "--driver-mode=cl", "--target=i686-pc-windows-msvc", "/nologo", "/c", "/O2", "/MT", "/EHsc", "/utf-8",
        "/W0", "/DNDEBUG", "/D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH", "-fms-compatibility-version=19.40",
        "-Wno-everything"] + SYS
XN = SRC / "external/xNVSE"
core = ["/std:c++latest", "/I", str(SRC / "src"), "/I", str(SRC / "external/enet/include"), "/DWIN32_LEAN_AND_MEAN",
        "/DNOMINMAX"]
plug = core[:-2] + ["/I", str(XN), "/I", str(XN / "nvse"), "/I", str(XN / "nvse/nvse"), "/DRUNTIME",
                    "/DRUNTIME_VERSION=0x040020D0", "/D_WINDOWS", "/D_USRDLL", "/FInvse/prefix.h"]
FAKE = os.environ.get("FAKEFRIEND")
units = [(c, ["/I", str(SRC / "external/enet/include"), "/D_WINSOCK_DEPRECATED_NO_WARNINGS", "/D_CRT_SECURE_NO_WARNINGS"])
         for c in sorted((SRC / "external/enet").glob("*.c"))]
units += [(SRC / s, core) for s in target_sources("nvcoop_core")]
if FAKE:
    units.append((SRC / "tools/fakefriend/main.cpp", core))
    fake = HERE / "fake_coop.cpp"  # optional build-only coop.cpp for the test host (see stress notes)
    if fake.exists():
        units = [(fake, core + ["/I", str(SRC / "src/coop")]) if u[0] == SRC / "src/coop/coop.cpp" else u for u in units]
else:
    units += [(SRC / s, plug) for s in target_sources("NVCoop")]
    units.append((HERE / "stub_setmodelpath.cpp", plug))


def compile_one(u):
    src, flags = u
    name = str(src.relative_to(SRC)) if src.is_relative_to(SRC) else src.name
    obj = OBJ / (name.replace("/", "_") + ".obj")
    if obj.exists() and obj.stat().st_mtime > src.stat().st_mtime and not os.environ.get("FULL"):
        return obj, None
    r = subprocess.run(BASE + flags + [str(src), f"/Fo{obj}"], capture_output=True, text=True)
    return obj, (r.stderr + r.stdout) if r.returncode else None


errs, objs = 0, []
with cf.ThreadPoolExecutor(os.cpu_count()) as ex:
    for obj, err in ex.map(compile_one, units):
        objs.append(obj)
        if err:
            errs += 1
            print("ERROR", obj.name, "\n", err[:3000])
print(f"{len(units)} units, {errs} failed")
if errs:
    sys.exit(1)
target = OUT / ("fakefriend.exe" if FAKE else "NVCoop.dll")
link = ["lld-link", "/nologo"] + (["/SUBSYSTEM:CONSOLE"] if FAKE else ["/DLL", f"/DEF:{SRC / 'src/exports.def'}"]) + [
    "/MACHINE:X86", f"/OUT:{target}", f"/MAP:{OUT / (target.stem + '.map')}", "/OPT:REF", "/OPT:ICF", "/SAFESEH:NO",
    f"/LIBPATH:{X / 'crt/lib/x86'}", f"/LIBPATH:{X / 'sdk/lib/um/x86'}", f"/LIBPATH:{X / 'sdk/lib/ucrt/x86'}",
    "ws2_32.lib", "winmm.lib", "dbghelp.lib", "psapi.lib", "user32.lib", "kernel32.lib", "ole32.lib", "oleaut32.lib",
    "shell32.lib", "advapi32.lib", "gdi32.lib", "bcrypt.lib", "crypt32.lib", "uuid.lib", "sapi.lib", "winhttp.lib",
    "dsound.lib", "dxguid.lib", "version.lib", "comctl32.lib"] + [str(o) for o in objs]
r = subprocess.run(link, capture_output=True, text=True)
print(r.stdout[-3000:], r.stderr[-6000:])
print("linked" if r.returncode == 0 else "LINK FAILED", target if target.exists() else "")
sys.exit(r.returncode)
