// True Co-op Fixes, Linux build only: clang devirtualizes e->model.SetModelPath(...) into a direct call, MSVC calls
// it through the game's vtable. Same behaviour as MSVC: call TESModel's vtable slot 6 (the game's own function).
#include "nvse/GameForms.h"
void TESModel::SetModelPath(char* path)
{
    using Fn = void(__thiscall*)(TESModel*, char*);
    (*reinterpret_cast<Fn**>(this))[6](this, path);
}
