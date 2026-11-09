# C177 • Use an existing environment to review an editable physical object

## Product decision

An agent can bring parts from different 3D tools into one scene. What should survive the trip is the meaning of the authored object. For the service cart, that includes which object moves, which four corners set its deck width, the units of that edit, and the measured gap to each side of the gate. A view of the cart in a real workshop would help a person review the motion. The exported cart and gate geometry supplies the evidence for clearance.

The November 9 owner-supplied Frontier 3D brief selects read-only input of an existing Gaussian-splat GLB, a binary glTF file that stores a scene. A Gaussian splat describes how a small volume contributes color and opacity to an image. Many splats together can reproduce the appearance of a photographed space. They can obscure part of a cart from one viewpoint without defining a surface on which the cart can drive.

| Who supplies the information? | What an agent can rely on |
| --- | --- |
| Editable OntoKin source | Part identity, units, relationships, authorized edits and intended behavior for the supported language profile. Rebuild the authored recording after an edit. |
| Authored GLB and passage checker | The geometry and motion actually delivered. Check the accepted source and both measured gaps on every variant. |
| Existing splat GLB | Appearance for visual review. Record where the file came from, its digest and the limits of the reader. |
| Registration manifest | Which files belong together and how to place the environment in the authored metre frame. Inspect anchor errors separately from geometry measurements. |
| Future collision proxy | Any physical use of captured surroundings needs a separately identified proxy, a metric error bound and an independent acceptance test for the proposed use. |

## Delivery sequence and acceptance

1. **Make the two layers independently testable.** Check the splat file before rendering. Bind the environment, alignment, editable source and authored GLB to a manifest. Exercise the source edit against a controlled scene, reject bad inputs and compare measured geometry. The [experimental viewer and builders](../../../examples/splat-composite/README.md) are the entry point.
2. **Qualify a captured environment.** Select one existing, redistribution-cleared, uncompressed capture in the supported profile. Retain its original URL, author, license, digest, byte and splat counts. Use at least three non-collinear paired points with named physical features. Record how the world measurements were made, their uncertainty, and a tolerance chosen before registration. Report each residual, the maximum and RMS error. A synthetic identity transform is a software control.
3. **Test what a reviewer sees.** Use a fixed camera and a foreground feature. Capture the cart in front of, partly behind, and behind it. Compare against environment-off images at the same poses. Swap cart variants and check that the environment and alignment stay fixed. For each exercised backend record parse time, time to first composite frame, median/p95 frame time, viewport and sample size. Distinguish software rendering from GPU measurements. A viewer pass does not qualify a game engine or live dynamics.
4. **Decide whether to expand.** Run the agent comparison below before undertaking a general import system, a second production backend or a capture pipeline. A later adapter can target Blender, a CAD kernel or a physics engine if a concrete object needs it. Give each adapter a supported profile, an identity/units mapping and an independent destination check.

## Direct-tool comparison

Use the existing service entrance to debug the protocol, then hold out an unseen mechanical assembly and edit. Freeze the prompt and acceptance checks before either run. Give the same agent model, tool budget, source information, units, environment bytes, time allowance and output requirements to both routes. One route edits OntoKin and uses the composite viewer. The other uses Blender/Python with the same opportunity to inspect, edit and render. Permit persistent scripts and names in both routes. Keep the held-out input away from example-specific code.

Ask the agent to identify the moving part, change one dimension, repair a deliberately broken clearance, and create a second reusable variant. Apply one independent test to both deliveries. Check target dimensions, gaps through the full passage, preserved identities and motion of unrelated parts. Blind the visual review to the tool used when practical. Record prior setup separately from work on the task. Retain the model/version, tool versions, prompt, transcripts, source revisions, token counts, wall time, retries and human interventions, including failed attempts.

If the trials show reliable repairs at competitive cost, extend to a proposed cohort of 10–20 mechanical objects and test a second destination. If both approaches meet the checks with comparable effort, keep the small contract and investigate which features earn their upkeep. If the direct tool reliably does better, narrow the language investment to the semantics or checks that showed a measurable benefit. A scripted cart run establishes a regression fixture. Agent performance and cost require their own trials.

## References

- [Ratified Khronos Gaussian splatting extension](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_gaussian_splatting/README.md)
- [Three.js loader registration](https://threejs.org/docs/pages/GLTFGaussianSplatLoaderExtension.html) and [GaussianSplat renderer support](https://threejs.org/docs/pages/GaussianSplat.html)
- [OntoKin service-entrance source and independent measurement](../../../examples/service-entrance/README.md)
- [OntoKin export and playback contract](../OK-ENG-002-3d-scene-animation-export-and-visual-validation.md)
