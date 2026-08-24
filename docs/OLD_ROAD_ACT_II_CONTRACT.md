# The Old Road — Act II Contract

## Status

Act II is **designed but dormant**. It must not appear in the active runtime while `old_barrow_interior` is absent from `bre-thiar-assets-v2.json`.

The shipped save contract remains authoritative until the production interior opens:

- quest id: `old_road`
- threshold completion stage: `4`
- status: `completed`
- earned reward: `Rowan Charm`
- save key: `bre-thiar-hypnobius-v3`

This protects existing QA saves. Opening the barrow later must extend those saves instead of resetting or silently replacing them.

## Activation migration

When `old_barrow_interior` becomes a live zone, the same production change must add an explicit `migrateOldRoadAct2` runtime hook.

That migration must:

1. recognize an existing `old_road` stage-4 completion;
2. preserve the already-earned Rowan Charm;
3. reopen The Old Road into its second act only when the interior is actually available;
4. never reset class, gender, HP, player position, or unrelated world state;
5. remain idempotent so loading the same save repeatedly cannot duplicate rewards or skip objectives.

The exact internal quest-state representation may evolve, but the above behavioral contract is permanent.

## Map-backed Act II sequence

`maps/Old_Barrow_Interior_v1.tmj` must declare:

`quest_contract=old_road_act2_v1`

The `Spawns & Triggers` layer must contain objects whose `quest_step` properties cover these semantic checkpoints:

1. `old_road_act2_entry` — entering the awakened barrow and establishing the new objective.
2. `old_road_act2_objective_1` — first exploration/objective room.
3. `old_road_act2_objective_2` — second distinct exploration/objective room.
4. `old_road_act2_warden` — the Stonebound Warden objective.
5. `old_road_act2_deeper_seal` — authored endpoint after the encounter; future depth remains sealed.

The two objective rooms may be named and dressed however best suits the final map. These identifiers are gameplay metadata, not player-facing room names.

## Stonebound Warden

The interior map must contain exactly one `encounter` trigger with:

`encounter_id=stonebound_warden`

The encounter is an entity/system encounter, never painted into environment art.

The Warden hall must be spatially readable enough for future combat telegraphs and movement. The quest should not complete merely by reaching the room; completion must be driven by actual encounter resolution once combat exists.

## Reward continuity

The Rowan Charm is an Act I-earned item and must remain owned after Act II activates.

Act II may add a later reward, but must not retroactively remove, rename, or re-award the Rowan Charm. Any new reward should be represented separately so old saves cannot receive duplicate stage-4 rewards.

## Validation

Run:

```bash
python tools/validate_old_road_act2_contract.py
```

The validator is state-aware:

- **SEALED:** verifies the shipped stage-4 completion/save behavior remains intact and that no live Act II tokens have leaked into the runtime.
- **ACTIVE:** requires the interior quest contract, two map-backed exploration objectives, the Stonebound Warden encounter trigger, the deeper sealed endpoint, a save-migration hook, and Rowan Charm continuity.

## Do not do

- Do not reset existing quest saves when Act II launches.
- Do not convert the Rowan Charm into an Act II reward.
- Do not make the Stonebound Warden a decorative map object.
- Do not hard-code objective locations outside Tiled.
- Do not expose Act II through the legacy renderer.
- Do not mark the quest complete on room entry before the encounter is resolved.
