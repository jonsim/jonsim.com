---
title: 'Primitives' Short: Deconstruction
date: 2014-02-14
description: A write up of the techniques used in my short film 'Primitives'.
tags: 3D Modelling, Animation
---

On this page I break down the individual items used in my short film 'Primitives', along with details of their construction.

## The Set

![](images/primitives_set.jpg)

The set is designed to look like the interior of an ageing shed. The wooden boards making up the walls, roof and floor are all simple cuboids which have been (dis)placed by hand. Ideally I would have liked to add displacement maps to these to make them look slightly more beaten up and less perfect, but I was able to texture them to appear antiquated. Five different diffuse maps are used for the boards making up the walls and ceiling to avoid obvious repetition.

The workbench was one of the more challenging models to make as I knew it would feature in numerous close-ups from different angles. I wanted to give it an old and beaten-up look, something I achieved using Maya's sculpting tool which, while not perfect (especially around angular edges) and quite slow to work with, did a good job of achieving the desired effect. This effect was continued to both legs (the thicker one and the thinner legs which are all the same model, just rotated different amounts). In order to texture the table I baked out a displacement map relative to the original cuboid shape, giving a mask of the areas that had been weathered away. This was used to make the exposed wood a different colour and texture. An AO map was also baked out to give an idea of where grime would collect on the surface; taking special care to make the points the legs connected look realistic. Various paint splatters and dust markings were finally added to give the table some history.

## Butterfly

![](images/primitives_butterfly.jpg)

The butterfly, which acts as the initiator for the story arc in the short, was modelled with NURBS to create a complex and flexible wing shape. The central body (which needed to be little more than a cylinder since it was never seen in closeup) had a small amount of fur applied to it to break up the otherwise unnaturally clean lines. The animation rig for the butterfly was one of the most complex made for the short in order to achieve a realistic flight motion: ensuring the different parts of the butterfly's wings moved correctly. Sadly, while the flapping animation was near perfect, the actual movement the butterfly executed was not as realistic as I would have liked.

## Caliper

![](images/primitives_caliper.jpg)

Based on a pair of medical calipers (probably one of the more tenuous items to naturally occur in a garden shed), the calipers act as the creature's ribs and are variously resized to appear anatomically correct.

## Can

![](images/primitives_can.jpg)

## Lamp

![](images/primitives_lamp.jpg)

## Nuts and Bolts

![](images/primitives_nuts_bolts.jpg)

## Penknife

![](images/primitives_penknife.jpg)

## Toolbox

![](images/primitives_toolbox.jpg)

## Torch

![](images/primitives_torch.jpg)

## Trowel

![](images/primitives_trowel.jpg)
