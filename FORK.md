# True Co-op Fixes

**Based on [New Vegas Co-op](https://github.com/Zyrcxies/NewVegasCoop) by Zyrcxies.** This is a modified version,
not the official New Vegas Co-op. Same license (LICENSE): use, change and share it on those terms.

Built on 0.1.11; it plays with the official 0.1.11 (same protocol). Changes:

- **Safe removal of co-op references (fixes crashes).** `game::Remove()` disabled a reference and marked it for
  deletion in the same frame, while the game could still be updating or drawing its 3D. That crashed joiners when a
  copy of the host's NPC was removed (EXCEPTION_ACCESS_VIOLATION at FalloutNV.exe 0x5B1BB6, scene graph update of the
  removed copy's skeleton) and is the suspected cause of the host's renderer crash at 0xB706B8 / 0xB9DC0C (a deleted
  NiRefObject still queued for drawing) while friends' item pickups were applied. Now `Remove()` disables at once and
  `game::FlushRemovals()` (called every frame) marks the reference for deletion only once its 3D is gone and at least
  3 s have passed (30 s at most). This covers NPC copies, stand-ins, world items and mines.

- **0.1.11-fixes.2: no unsafe teleports (physics freeze).** Both games froze in combat with the physics world
  holding NaN / ~1e19 coordinates (an endless Havok broadphase loop at FalloutNV.exe 0xD16AEB the next time anything
  cast a ray). `Move()`, `MoveItem()` and `TravelTo()` now refuse positions that are not finite or lie far outside any
  world, and never SetPos a dead or knocked-out actor (the ragdoll owns its body then). Every refusal is logged
  ("Moves: refused ...") so the cause can be confirmed from NVCoop.log.
