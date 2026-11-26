# GeneWire visual identity

Original geometric assets combine an angular DNA helix, linked nodes, and bounded
data units. Graphite surfaces, lime accents, and neutral diagram backgrounds keep
the identity technical and readable on GitHub's light and dark themes. No stock
photography, external logos, remote image dependencies, or bundled fonts are used.

| Asset | Use |
| --- | --- |
| [logo.svg](logo.svg) | Default wordmark on a fixed light surface |
| [logo-light.svg](logo-light.svg) | Light-theme wordmark |
| [logo-dark.svg](logo-dark.svg) | Dark-theme wordmark |
| [icon.svg](icon.svg) | Standalone helix/network mark |
| [banner.svg](banner.svg), [banner.png](banner.png) | README banner, 1280 × 360 |
| [social-preview.svg](social-preview.svg), [social-preview.png](social-preview.png) | Editable social card and exact 1280 × 640 PNG |

Original assets use [Apache-2.0](../../LICENSE). No exclusive trademark rights or
external endorsements are asserted. SVG text uses system sans-serif fallbacks;
font metrics may vary slightly between platforms. PNGs capture the reviewed render.
SVGs contain accessible titles and descriptions and no executable content.

## Editing and rendering

Edit the SVG source first. Preserve its viewBox, semantic labels, contrast, and
fixed background. Regenerate the matching PNG when changing a banner or social
card. Raster previews were produced with `@resvg/resvg-js` using system fonts;
that renderer is a temporary validation tool, not a project runtime dependency.
Review both the SVG and PNG visually. There is no repository asset-build command
or CI workflow at bootstrap.

The diagrams in [../diagrams](../diagrams) are explicitly conceptual. Update their
meaning alongside the README and decision register whenever the design changes.

## Set the GitHub social preview

The card is prepared locally; it has not been uploaded through the API. A
maintainer can open the repository's **Settings → General → Social preview**,
choose **Edit → Upload an image**, and select `social-preview.png` from this
directory. Verify the crop before saving. This is a repository social card, not
a user avatar or README image.

See [GitHub's social preview instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).
