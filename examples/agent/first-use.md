# Can a coding agent make its first OntoKin edit?

This proposed product milestone tests a claim a user can check. Give a coding agent a motion brief and an editable scene. Can it change the intended object, preserve its sibling, and deliver an animation that shows the requested behavior?

## For the agent

Start from the [two-assembly scene](authoring-demo.ok) on a checkout identified by its commit. Use Python 3.11 or later and a fresh local store. The source profile is `core-0.1`, the request protocol is `ontokin.agent/0.1`, and the recorded animation target is `ontokin.glb/0.1`. These identify the interfaces used by this exercise. The Python package has its own version.

The [request schema](../../docs/language-design/agent-v0.1/request.schema.json) lists required fields and operations. The [agent guide](README.md#use-the-agent-interface-directly) shows how to issue a request and wait for its result. Use the service to inspect, edit, evaluate, export and retrieve. Save the accepted `.ok` source and the retrieved `.glb` file.

## For the person running the trial

1. For a control, run the [scripted demonstration](README.md#reproduce-the-workflow) from the same commit. Keep its solution and outputs outside the agent's trial materials.
2. Write down a new prompt and expected results before the session. Specify an instance to resize, a motion change with a distance and time, and an object or action that must keep its original behavior. Give the agent the prompt and public documentation. Fix the allowed tools and record any extra hints.
3. Time setup from a fresh checkout and time the task separately. Save the requests, failures, retries, accepted source and animation. Check the source diff for the scope of the edit. Compare the delivered mesh dimensions and world poses at the chosen times with the expectations using an independent reader. Open the exported file in the [offline viewer](../visual/viewer.html) and inspect playback there.
4. Record the commit, Python and viewer versions, time to first correct playback, help required, and the first point of confusion. A fast export with the wrong object or motion is a failed trial. Record any missing checks explicitly.

## Proposed milestone decision

Run two previously unseen edit briefs in fresh agent sessions. For a third brief, give an agent supported parts and ask it to author a small moving assembly from a written description. That last task tests source creation as well as editing. Have one person outside the development session attempt the first-run instructions from a fresh checkout.

Aim for correct, independently checked output on all three briefs without maintainer hints, and a first correct playback for the newcomer within 15 minutes. These are targets for this milestone. If a trial fails, fix the first reproducible obstacle and repeat with a new brief. If the trials pass, repeat the exercise on the [keyed mechanical assembly](../construction/README.md) before proposing a packaged preview. Keep trial results separate from the [physics and release acceptance record](../../STATUS.md).
