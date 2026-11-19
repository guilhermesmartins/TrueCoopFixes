# Building on Linux (no Visual Studio)

Used for True Co-op Fixes builds. Needs clang 18+ (MSVC mode), lld-link, Python 3, and the MSVC CRT + Windows SDK
downloaded by [cargo-xwin](https://github.com/rust-cross/cargo-xwin) (you accept Microsoft's license when doing so):

    XWIN_ACCEPT_LICENSE=true XWIN_ARCH=x86 XWIN_CACHE_DIR=~/Projects/toolchains/xwin-x86 \
        cargo xwin env --target i686-pc-windows-msvc
    git submodule update --init --recursive
    python3 tools/linux-build/build.py build-linux        # -> build-linux/NVCoop.dll (+ NVCoop.map)
    FAKEFRIEND=1 python3 tools/linux-build/build.py build-fake   # -> the fakefriend test tool

`stub_setmodelpath.cpp` keeps one call going through the game's vtable as MSVC does.
