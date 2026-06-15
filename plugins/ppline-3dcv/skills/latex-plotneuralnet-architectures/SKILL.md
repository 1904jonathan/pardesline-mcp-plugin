---
name: latex-plotneuralnet-architectures
description: "Use this skill to generate publication-ready neural-network architecture diagrams in LaTeX/TikZ with PlotNeuralNet (HarisIqbal88) — the 3D box-and-arrow style seen in CNN/segmentation papers (AlexNet, VGG, FCN, U-Net, ResNet, ViT). Triggers: 'PlotNeuralNet', 'neural network diagram', 'architecture figure', 'draw my CNN/U-Net/ResNet/ViT/encoder-decoder', '3D conv block diagram', 'tikzeng', 'to_Conv/to_Pool/to_SoftMax', or any request to visualize a deep-learning architecture as a paper/slide figure. It details the Python API (tikzeng.py primitives, blocks.py blocks), the underlying TikZ pic styles (Box, RightBandedBox, Ball), colors, named coordinates, connections/skip connections, the coordinate/offset positioning model, the tikzmake build process, and complete worked architectures. It SHIPS tested companion Python in assets/: pnn_ext.py (modern layer helpers — BatchNorm, Dropout, FC, GAP, Attention, Transformer, Concat, Embedding) and model_zoo.py (ready-to-run generators for LeNet, AlexNet, VGG16, ResNet, U-Net, encoder-decoder, ViT, autoencoder), all compiled and verified to render. Produces both the Python generator and the raw .tex, and the resulting PDF embeds into papers/slides. Consult latex-paper-ieee / latex-beamer-scientific / latex-venue-standards for the surrounding document."
---

# Neural-Network Architecture Diagrams with PlotNeuralNet

PlotNeuralNet (HarisIqbal88, MIT) renders neural networks as **3D boxes connected by arrows** — the canonical look of CNN/segmentation papers. Two ways in: a **Python generator** that emits a `.tex` file, or **hand-written TikZ** using the same `\pic` styles. This skill covers both, the full API, the positioning model, and complete worked architectures.

When the resulting diagram is embedded in a paper or slides, also consult `latex-paper-ieee` / `latex-beamer-scientific` (the output is a standalone PDF you `\includegraphics`).

## 0. How the system is layered (mental model)

```
your_arch.py  (you write this)
   └─ imports pycore/tikzeng.py   → primitive layer functions: to_Conv, to_Pool, ...
   └─ imports pycore/blocks.py    → composite blocks: block_2ConvPool, block_Unconv, block_Res
        ↓ to_generate(arch, "your_arch.tex")
your_arch.tex (generated)
   └─ \input layers/init.tex      → loads Box.sty, RightBandedBox.sty, Ball.sty + colors + arrows
        ↓ pdflatex (standalone class)
your_arch.pdf  → \includegraphics into paper/slides
```

Each `to_*` Python function just returns a **string of TikZ** (a `\pic{...}` or `\draw{...}`). `arch` is a Python **list of these strings**; `to_generate` concatenates them into a `.tex`. So everything the Python does, you can also write directly as TikZ.

## 1. Install & build

```bash
git clone https://github.com/HarisIqbal88/PlotNeuralNet.git
cd PlotNeuralNet
# LaTeX deps (Ubuntu):
sudo apt-get install texlive-latex-base texlive-fonts-recommended \
                     texlive-fonts-extra texlive-latex-extra
# Windows: install MiKTeX + a bash runner (Git Bash / Cygwin)
```

Build a diagram (the repo ships `tikzmake.sh`, which runs the Python then pdflatex then cleans aux files):
```bash
cd pyexamples
bash ../tikzmake.sh my_arch        # NOTE: no ".py" extension — pass the basename
```
`tikzmake.sh` essentially does: `python my_arch.py` → produces `my_arch.tex` → `pdflatex my_arch.tex` → removes `.aux/.log/...`. If bash isn't available, run the two steps manually:
```bash
python my_arch.py                  # writes my_arch.tex
pdflatex my_arch.tex               # writes my_arch.pdf
```
The diagram compiles with `\documentclass[border=8pt, multi, tikz]{standalone}`, so the PDF is tightly cropped and ready to `\includegraphics`.

### 1b. Build via the ppline-3dcv MCP — no repo clone, no local LaTeX

You do **not** need to clone PlotNeuralNet or install LaTeX. This skill bundles the upstream
`pycore/` (tikzeng + blocks) in `assets/`, and the `ppline-3dcv` MCP server bundles the
`layers/` styles. End-to-end:

1. **Generate the `.tex`** locally with the bundled Python (run from this skill's `assets/`,
   where `pycore/`, `pnn_ext.py`, `model_zoo.py` sit together — the `pycore` import resolves
   with no repo clone):
   ```bash
   python model_zoo.py unet            # writes unet.tex (or build your own arch)
   ```
   Keep `to_head('..')` as usual — the server stages `layers/` to match that `../layers/` path.
2. **Compile server-side** by passing the generated `.tex` content to the MCP tool with the
   asset bundle:
   ```
   compile_latex(source=<contents of unet.tex>, assets=["plotneuralnet"])
   ```
   It returns `{ok, pdf_url, tex_url}` (Tectonic auto-fetches `standalone`/`import`/`tikz`).
   On `{ok:false, log_tail}`, fix the arch/source and call again.
3. **Embed** the returned PDF in a paper/deck (§12). MCP-tool reference:
   `ppline-3dcv:research-and-presentations`; writing layer: `latex-scientific-core`.

(Local pdflatex / `tikzmake.sh` still works if the user has a TeX install — both paths
produce the same cropped PDF.)

## 2. tikzeng.py — the primitive API (exact signatures)

A standard generator file:
```python
import sys
sys.path.append('../')             # so `pycore` is importable
from pycore.tikzeng import *

arch = [
    to_head('..'),                 # \documentclass + \input layers/init.tex (projectpath = repo root)
    to_cor(),                      # color definitions (\ConvColor, \PoolColor, ...)
    to_begin(),                    # \begin{document}\begin{tikzpicture} + connection styles
    # ... layers go here ...
    to_end(),                      # \end{tikzpicture}\end{document}
]

def main():
    namefile = str(sys.argv[0]).split('.')[0]
    to_generate(arch, namefile + '.tex')

if __name__ == '__main__':
    main()
```

### Document scaffolding
| Function | Role |
|----------|------|
| `to_head(projectpath)` | Emits the standalone `\documentclass` and `\input{<projectpath>/layers/init.tex}`. `projectpath` is the **relative path to the repo root** (usually `'..'` from `pyexamples/`). |
| `to_cor()` | Defines the layer colors (see §4). |
| `to_begin()` | Opens `tikzpicture`, defines `connection`/arrow styles. |
| `to_end()` | Closes picture + document. |
| `to_generate(arch, pathname="file.tex")` | Joins the list and writes the `.tex`. |

### Input image
```python
to_input(pathfile, to='(-3,0,0)', width=8, height=8, name="temp")
```
Places an image (e.g. the sample input) on the `zy` plane at `to`. Used as the visual "input" at the far left.

### Layer primitives (full signatures — memorize the parameter order)
```python
to_Conv(name, s_filer=256, n_filer=64, offset="(0,0,0)", to="(0,0,0)",
        width=1, height=40, depth=40, caption=" ")

to_ConvConvRelu(name, s_filer=256, n_filer=(64,64), offset="(0,0,0)", to="(0,0,0)",
                width=(2,2), height=40, depth=40, caption=" ")   # two stacked conv widths

to_Pool(name, offset="(0,0,0)", to="(0,0,0)",
        width=1, height=32, depth=32, opacity=0.5, caption=" ")

to_UnPool(name, offset="(0,0,0)", to="(0,0,0)",
          width=1, height=32, depth=32, opacity=0.5, caption=" ")

to_ConvRes(name, s_filer=256, n_filer=64, offset="(0,0,0)", to="(0,0,0)",
           width=6, height=40, depth=40, opacity=0.2, caption=" ")

to_ConvSoftMax(name, s_filer=40, offset="(0,0,0)", to="(0,0,0)",
               width=1, height=40, depth=40, caption=" ")

to_SoftMax(name, s_filer=10, offset="(0,0,0)", to="(0,0,0)",
           width=1.5, height=3, depth=25, opacity=0.8, caption=" ")

to_Sum(name, offset="(0,0,0)", to="(0,0,0)", radius=2.5, opacity=0.6)
```

### Connections
```python
to_connection(of, to)      # straight arrow from <of>-east to <to>-west
to_skip(of, to, pos=1.25)  # curved skip/residual arrow over the top (pos = arc height factor)
```

**Parameter semantics (this is the crux):**
- `name` — unique node id. It becomes the TikZ pic name, exposing coordinates `name-east`, `name-west`, etc.
- `s_filer` — the **spatial** size shown as the `zlabel` (e.g. feature-map side length like 256, 128…). Printed along the depth edge.
- `n_filer` — the **number of channels/filters**, shown as `xlabel` on top (e.g. 64, 128). A tuple `(64,64)` draws two stacked sub-boxes (`to_ConvConvRelu`).
- `width` — **visual** thickness of the box in the x-direction (scales with channel count by convention, *not* literally). Tuple for multi-box.
- `height`, `depth` — **visual** y/z size (scale with the feature-map resolution by convention; halve them each time you pool).
- `offset` — displacement **from** the `to` anchor before placing this layer (e.g. `"(1,0,0)"` leaves a gap; `"(0,0,0)"` butts it flush).
- `to` — the anchor coordinate this layer attaches to, almost always `"(<prevname>-east)"`.
- `caption` — text printed under the block.
- `opacity` — fill transparency (pooling/softmax use <1 to look lighter).

## 3. blocks.py — composite blocks (less code for repeating patterns)

```python
from pycore.blocks import block_2ConvPool, block_Unconv, block_Res
```
Each returns a **list**; splice it into `arch` with the `*` operator.

```python
block_2ConvPool(name, botton, top, s_filer=256, n_filer=64,
                offset="(1,0,0)", size=(32,32,3.5), opacity=0.5)
# → ConvConvRelu + Pool + connection. Encoder stage (VGG/U-Net down-path).

block_Unconv(name, botton, top, s_filer=256, n_filer=64,
             offset="(1,0,0)", size=(32,32,3.5), opacity=0.5)
# → UnPool + ConvRes + Conv + ConvRes + Conv + connection. Decoder/up stage.

block_Res(num, name, botton, top, s_filer=256, n_filer=64,
          offset="(0,0,0)", size=(32,32,3.5), opacity=0.5)
# → `num` Conv layers + connections + a to_skip residual arc. ResNet block.
```
Note the repo's parameter is spelled **`botton`** (not "bottom") — match it exactly. `size=(height, depth, width)`.

Usage:
```python
arch = [
    to_head('..'), to_cor(), to_begin(),
    to_input('../examples/fcn8s/cats.jpg'),
    *block_2ConvPool(name='b1', botton='input', top='p1', s_filer=256, n_filer=64,  offset="(0,0,0)",  size=(32,32,2.5)),
    *block_2ConvPool(name='b2', botton='p1',    top='p2', s_filer=128, n_filer=128, offset="(1,0,0)",  size=(25,25,3.5)),
    to_end(),
]
```

## 4. Colors (to_cor) and how to recolor

`to_cor()` defines these (TikZ `rgb:` mixing — `rgb:color1,weight1;color2,weight2;...`):
```latex
\def\ConvColor{rgb:yellow,5;red,2.5;white,5}
\def\ConvReluColor{rgb:yellow,5;red,5;white,5}
\def\PoolColor{rgb:red,1;black,0.3}
\def\UnpoolColor{rgb:blue,2;green,1;black,0.3}
\def\FcColor{rgb:blue,5;red,2.5;white,5}
\def\FcReluColor{rgb:blue,5;red,5;white,4}
\def\SoftmaxColor{rgb:magenta,5;black,7}
\def\SumColor{rgb:blue,5;green,15}
```
To recolor a whole figure, override these *after* `to_cor()` by appending a raw string to `arch`, e.g.:
```python
arch += [r"\def\ConvColor{rgb:blue,5;red,1;green,1;black,3}"]
```
Edge color & arrow (from `init.tex`): `\def\edgecolor{rgb:blue,4;red,1;green,4;black,3}` and `\midarrow` (a Stealth arrow used as the node on connection paths).

## 5. The TikZ layer underneath (for hand-writing or customizing)

Every `to_*` emits a `\pic`. Three pic styles exist (in `layers/*.sty`):

- **`Box`** — plain 3D rectangular prism. Used by `to_Pool`, `to_UnPool`, `to_SoftMax`, FC layers.
- **`RightBandedBox`** — box with a colored band on its right face (the ReLU band). Used by `to_Conv`/`to_ConvConvRelu`/`to_ConvRes`.
- **`Ball`** — a sphere, for `to_Sum` (element-wise add / concat junctions).

Raw `\pic` syntax (what `to_Conv` actually produces):
```latex
\pic[shift={(0,0,0)}] at (prevlayer-east)
  {Box={name=conv2, caption=Conv,
        xlabel={{64, }}, zlabel=128,
        fill=\ConvColor, height=32, width=2, depth=32}};
```
`RightBandedBox` adds `bandfill=\ConvReluColor` and accepts an `xlabel` **tuple** `{{"64","64"}}` for the two stacked widths.

**Box parameters** (defaults): `width=2`, `height=13`, `depth=15`, `scale=0.2`, `fill=rgb:red,5;green,5;blue,5;white,15`, `opacity=0.4`, plus label arrays `xlabel`/`ylabel`/`zlabel`/`caption`/`name`. A `width` *array* `{2,2,2}` draws several concatenated boxes (parallel branches / stacked convs).

### Named coordinates (the key to connections)
Each named pic exposes anchors you draw to/from:
`name-east`, `name-west`, `name-north`, `name-south`, `name-anchor` (center), `name-near` (front), `name-far` (back), and corners `name-northeast`, `name-northwest`, `name-southeast`, etc. Connections almost always go `(<a>-east)` → `(<b>-west)`.

Hand-written connection / skip:
```latex
\draw [connection] (conv1-east) -- node {\midarrow} (pool1-west);

% skip (residual) arc up and over:
\path (cr3-southeast) -- (cr3-northeast) coordinate[pos=1.25] (cr3-top);
\draw [copyconnection] (cr3-northeast) -- node {\copymidarrow} (cr3-top)
      -- node {\copymidarrow} (skipdest-north -| cr3-top) -- ...;
```
U-Net's copy-and-crop uses a separate `copyconnection` style + `\copymidarrow` (a thicker blue arrow defined in the example preamble).

## 6. The positioning model (offsets & anchors) — internalize this

There is **no auto-layout**. You chain layers left-to-right by anchoring each to the previous one's `-east` and adding an `offset`:
- `to="(prev-east)"`, `offset="(0,0,0)"` → flush against the previous block.
- `offset="(1,0,0)"` → leaves a 1-unit gap (where the connection arrow is drawn).
- Branches (e.g. skip paths, two-stream nets) place a layer relative to an earlier node by name and use a y/z offset, e.g. `offset="(0,-4,0)"` to drop a parallel path below.
- For an encoder–decoder (U-Net), the decoder is placed by anchoring to the last bottleneck node and walking back up with positive x-offsets; skips are drawn with `to_skip`.

**Convention for sizes** (so the figure *reads* like a real CNN):
- Halve `height`/`depth` at every pool; double the box `width` as channels double.
- Keep `s_filer` = feature-map side (256→128→64…) and `n_filer` = channels (64→128→256…).

## 7. Worked example A — simple CNN (the repo's test_simple)

```python
import sys; sys.path.append('../')
from pycore.tikzeng import *

arch = [
    to_head('..'),
    to_cor(),
    to_begin(),
    to_Conv("conv1", 512, 64, offset="(0,0,0)",  to="(0,0,0)",        height=64, depth=64, width=2),
    to_Pool("pool1",            offset="(0,0,0)", to="(conv1-east)"),
    to_Conv("conv2", 128, 64, offset="(1,0,0)",  to="(pool1-east)",   height=32, depth=32, width=2),
    to_connection("pool1", "conv2"),
    to_Pool("pool2",            offset="(0,0,0)", to="(conv2-east)",  height=28, depth=28, width=1),
    to_SoftMax("soft1", 10, "(3,0,0)", "(pool2-east)", caption="SOFT"),
    to_connection("pool2", "soft1"),
    to_end(),
]

def main():
    namefile = str(sys.argv[0]).split('.')[0]
    to_generate(arch, namefile + '.tex')

if __name__ == '__main__':
    main()
```

## 8. Worked example B — VGG-style encoder via blocks

```python
import sys; sys.path.append('../')
from pycore.tikzeng import *
from pycore.blocks  import block_2ConvPool

arch = [
    to_head('..'), to_cor(), to_begin(),
    to_input('../examples/fcn8s/cats.jpg'),
    *block_2ConvPool(name='b1', botton='input', top='p1', s_filer=224, n_filer=64,
                     offset="(0,0,0)", size=(40,40,2.0)),
    *block_2ConvPool(name='b2', botton='p1', top='p2', s_filer=112, n_filer=128,
                     offset="(1,0,0)", size=(32,32,3.0)),
    *block_2ConvPool(name='b3', botton='p2', top='p3', s_filer=56,  n_filer=256,
                     offset="(1,0,0)", size=(25,25,4.0)),
    to_ConvSoftMax("soft1", 1000, offset="(1.5,0,0)", to="(p3-east)",
                   width=1, height=10, depth=10, caption="FC+Softmax"),
    to_connection("p3", "soft1"),
    to_end(),
]
def main():
    to_generate(arch, str(sys.argv[0]).split('.')[0] + '.tex')
if __name__ == '__main__': main()
```

## 9. Worked example C — U-Net (encoder–decoder + skips)

Pattern: down-path with `block_2ConvPool`, a bottleneck, up-path with `block_Unconv`, and explicit `to_skip` copy connections from each encoder stage to the mirrored decoder stage. The real `examples/Unet/Unet.tex` defines `copyconnection`/`\copymidarrow` and uses `\pic{RightBandedBox=...}` with `xlabel={{"512","512"}}` for the double convolutions, `zlabel=I/16` for resolution. Skeleton:
```python
import sys; sys.path.append('../')
from pycore.tikzeng import *
from pycore.blocks  import block_2ConvPool, block_Unconv

arch = [
    to_head('..'), to_cor(), to_begin(),
    to_input('../examples/fcn8s/cats.jpg'),
    # ----- Encoder -----
    *block_2ConvPool(name='b1', botton='input', top='p1', s_filer=512, n_filer=64,  offset="(0,0,0)",  size=(32,32,2.5)),
    *block_2ConvPool(name='b2', botton='p1',    top='p2', s_filer=256, n_filer=128, offset="(1,0,0)",  size=(25,25,3.0)),
    *block_2ConvPool(name='b3', botton='p2',    top='p3', s_filer=128, n_filer=256, offset="(1,0,0)",  size=(16,16,4.0)),
    # ----- Bottleneck -----
    to_ConvConvRelu("bottleneck", 64, (512,512), offset="(2,0,0)", to="(p3-east)",
                    width=(8,8), height=8, depth=8, caption="Bottleneck"),
    to_connection("p3", "bottleneck"),
    # ----- Decoder (mirror) -----
    *block_Unconv(name='b5', botton='bottleneck', top='end5', s_filer=128, n_filer=256, offset="(2.1,0,0)", size=(16,16,4.0)),
    *block_Unconv(name='b6', botton='end5',       top='end6', s_filer=256, n_filer=128, offset="(2.1,0,0)", size=(25,25,3.0)),
    *block_Unconv(name='b7', botton='end6',       top='end7', s_filer=512, n_filer=64,  offset="(2.1,0,0)", size=(32,32,2.5)),
    # ----- Output -----
    to_ConvSoftMax("soft1", 512, offset="(0.75,0,0)", to="(end7-east)", width=1, height=32, depth=32, caption="Output"),
    to_connection("end7", "soft1"),
    # ----- Skip (copy) connections, encoder → decoder -----
    to_skip(of='ccr_b1', to='ccr_res_b7', pos=1.5),
    to_skip(of='ccr_b2', to='ccr_res_b6', pos=1.5),
    to_skip(of='ccr_b3', to='ccr_res_b5', pos=1.5),
    to_end(),
]
def main():
    to_generate(arch, str(sys.argv[0]).split('.')[0] + '.tex')
if __name__ == '__main__': main()
```
`to_skip` references the internal node names the blocks create (`ccr_<name>` for the conv-conv-relu, `ccr_res_<name>` for the decoder residual conv). Inspect `blocks.py` to confirm the exact internal names for the version you cloned, then point `to_skip` at them.

## 10. Worked example D — ResNet residual block

```python
from pycore.tikzeng import *
from pycore.blocks  import block_Res
arch = [
    to_head('..'), to_cor(), to_begin(),
    to_Conv("conv1", 64, 64, offset="(0,0,0)", to="(0,0,0)", width=2, height=32, depth=32, caption="Conv"),
    *block_Res(num=2, name="res1", botton="conv1", top="res1_end",
               s_filer=64, n_filer=64, offset="(1.5,0,0)", size=(32,32,2.0)),
    to_end(),
]
```
`block_Res` lays down `num` conv layers in series and draws a `to_skip` arc from the block input over the top to the output — the identity shortcut.

## 11. Companion assets shipped with this skill (use these — they're tested)

This skill ships two ready-to-use Python files in `assets/`. **Prefer them over hand-writing** — both were generated, compiled to PDF against the real upstream `pycore` + layer `.sty` files, and verified to render.

### `assets/pnn_ext.py` — modern-layer extensions
Sits on top of `pycore/tikzeng.py` and adds the layer types the original lacks, emitting the same kind of TikZ strings so they drop straight into `arch`:
`to_BatchNorm`, `to_Dropout`, `to_FC`, `to_GAP`, `to_Attention`, `to_Transformer`, `to_Concat`, `to_Embedding`, a generic `to_LayerBox`, plus `extra_colors()` (append right after `to_cor()`) and chaining helpers `chain(...)` / `conv_bn_relu(...)`. Import with:
```python
import sys; sys.path.append('../')
from pycore.tikzeng import *
from pnn_ext import *          # this skill's extensions
```
**Important:** call `extra_colors()` in the arch list right after `to_cor()` so the new `\BnColor`, `\AttnColor`, etc. macros are defined before any extended layer uses them.

### `assets/model_zoo.py` — ready-to-run standard architectures
One command per model; each writes a `.tex` you compile with `pdflatex` (or `bash ../tikzmake.sh <name>`):
```bash
python model_zoo.py lenet            # then: pdflatex lenet.tex
python model_zoo.py alexnet
python model_zoo.py vgg16            # uses block_2ConvPool
python model_zoo.py resnet           # residual blocks + skip arcs (block_Res)
python model_zoo.py unet             # encoder-decoder + copy/skip (verified rendering)
python model_zoo.py encoder_decoder  # generic enc-dec (SegNet / registration backbone)
python model_zoo.py vit              # Vision Transformer: patch embed + transformer stack
python model_zoo.py autoencoder      # symmetric AE / VAE-style bottleneck
```
All eight compile to cropped PDFs ready to `\includegraphics`. They degrade gracefully if `pycore/blocks.py` is missing (manual fallbacks). Sizes follow the "halve H/D per downsample, grow width with channels" convention so the figures read like real networks — edit `s_filer`/`n_filer`/`height`/`depth`/`width` to match your actual layer dims.

**Setup:** this skill's `assets/` already bundles the upstream `pycore/` next to `pnn_ext.py`
and `model_zoo.py`, so just run them **from `assets/`** — `from pycore.tikzeng import *`
resolves with no repo clone (the script's own dir is on `sys.path`). The `sys.path.append('../')`
line in the examples is then a harmless no-op. Alternatively drop the files into a cloned repo's
`pyexamples/`. Compile the generated `.tex` either locally (`pdflatex`) or via the MCP
(`compile_latex(source, assets=["plotneuralnet"])`, §1b).

**Verified gotcha (baked into the zoo):** a `to_input(...)` image is a plain `\node` with **no `-east` anchor**, so a block/connection cannot attach to it directly (`! No shape named 'input-east'`). The zoo places a real `to_Conv("input", ...)` box as the first layer and connects blocks from that; copy this pattern for your own nets.

### Customizing a zoo model for your paper
1. Copy the relevant `build_<model>()` into your own script (or import it).
2. Rename layers and set real dimensions (`s_filer` = feature-map side, `n_filer` = channels).
3. Add/remove stages; insert `to_BatchNorm`/`to_Dropout`/`to_Attention` from `pnn_ext` where your architecture has them.
4. `to_generate(arch, "my_arch.tex")`, compile, embed (next section).

## 12. Embedding the result in a paper or presentation (the end-to-end goal)

The generated PDF is a tightly-cropped vector standalone — it drops into any LaTeX document. The full pipeline for a deliverable:

```
model_zoo.py / your arch.py  →  pdflatex  →  my_arch.pdf  →  copy into figures/  →  \includegraphics in paper.tex / slides.tex
```

### In a paper (IEEE/CVPR/NeurIPS/LNCS…)
```latex
\begin{figure}[t]\centering
  \includegraphics[width=\linewidth]{figures/my_arch.pdf}
  \caption{Proposed architecture. The encoder (left) downsamples while
           doubling channels; skip connections (top) feed the decoder.}
  \label{fig:arch}
\end{figure}
```
For a wide network that needs both columns, use a full-width float (`figure*`, top-only). See `latex-paper-ieee` §5 for two-column mechanics and `latex-venue-standards` for the venue's figure rules (e.g. CVPR wants color-blind-safe figures — don't rely on red/green alone; recolor via `extra_colors()` / `to_cor` overrides).

### In a Beamer presentation
Put the same PDF in a frame, usually beside bullet points in a `columns` block so the diagram and the talking points share the slide:
```latex
\begin{frame}{Architecture}
  \begin{columns}[T]
    \begin{column}{0.62\textwidth}
      \centering\includegraphics[width=\linewidth]{figures/my_arch.pdf}
    \end{column}
    \begin{column}{0.36\textwidth}
      \begin{itemize}
        \item Encoder–decoder backbone
        \item Skip connections preserve detail
        \item 3-stage downsampling
      \end{itemize}
    \end{column}
  \end{columns}
\end{frame}
```
To **reveal the network stage by stage** during the talk, generate several PDFs (encoder only, +bottleneck, +decoder) and overlay them:
```latex
\only<1>{\includegraphics[width=\linewidth]{figures/arch_stage1.pdf}}%
\only<2>{\includegraphics[width=\linewidth]{figures/arch_stage2.pdf}}%
\only<3>{\includegraphics[width=\linewidth]{figures/arch_full.pdf}}
```
(Build each by truncating the `arch` list at the relevant layer.) See `latex-beamer-scientific` for overlays, columns, and slide-design discipline.

### Recommended workflow when the user wants a paper/deck *with* a PlotNeuralNet figure
1. Read this skill + `latex-paper-ieee` **or** `latex-beamer-scientific` (and `latex-venue-standards` if a venue is named).
2. Pick/clone a `build_<model>()` from `model_zoo.py`; set real layer dimensions; add `pnn_ext` layers (BN/attention/etc.) as needed.
3. Generate and compile the figure PDF; place it in the document's `figures/`.
4. Build the paper/deck per the relevant skill; `\includegraphics` the PDF; write a caption that states what the figure *shows* (not just "architecture").
5. Keep the figure source (`my_arch.py`) in the repo so the diagram is reproducible and editable alongside the manuscript.

## 13. Troubleshooting & gotchas

- **`projectpath` wrong** → `\input` of `layers/init.tex` fails. From `pyexamples/` it is `'..'`. If you run your script elsewhere, set it to the relative path to the cloned repo root.
- **Pass the basename to `tikzmake.sh`** (`bash ../tikzmake.sh my_arch`, not `my_arch.py`).
- **Overlapping boxes** → increase `offset` x-component or shrink box `width`.
- **Connections to nowhere** → the `of`/`to` names in `to_connection`/`to_skip` must match a layer `name` (or an internal block node like `ccr_<name>`); a typo silently draws a broken/odd arrow.
- **Labels**: `s_filer`→`zlabel` (resolution), `n_filer`→`xlabel` (channels). Swapping them is the most common mislabel.
- **Compiler**: PlotNeuralNet targets **pdflatex** with the `standalone` class; no Python package install needed beyond cloning (it's plain scripts). The community fork `kgruiz/PlotNeuralNet` packages it as `pip`-installable with `from PlotNeuralNet.pycore import tikzeng` if you prefer an importable package.
- **Custom / modern layer types** (attention, transformer, BN, dropout, FC, GAP, concat): the upstream has no built-in pic for these — use **`assets/pnn_ext.py`** from this skill, which adds them as drop-in `to_*` helpers (remember `extra_colors()` after `to_cor()`). Or write a custom `\pic{Box=...}` and append it as a raw string to `arch`.
- **No auto-layout**: every position is manual via `offset`+anchor. Build incrementally, compiling after each stage.

## 14. Checklist

- [ ] Repo cloned; LaTeX packages installed; `projectpath='..'` correct.
- [ ] Used `assets/pnn_ext.py` for modern layers (with `extra_colors()` after `to_cor()`) and/or a `model_zoo.py` `build_<model>()` as the starting point.
- [ ] `arch` starts with `to_head/to_cor/to_begin` and ends with `to_end`.
- [ ] Each layer has a unique `name`; connections reference real names.
- [ ] `s_filer` (resolution) and `n_filer` (channels) labels are not swapped.
- [ ] Sizes follow the convention: halve height/depth at pools, grow width with channels.
- [ ] Skips point at the correct internal block node names (verified against your `blocks.py`).
- [ ] Builds via `bash ../tikzmake.sh <basename>` (or `pdflatex <name>.tex`) to a cropped PDF.
- [ ] PDF embedded as a vector figure with a meaningful caption and `\label`, in the paper (`figure`/`figure*`) or a Beamer `columns` frame.
- [ ] Figure source script kept in the repo for reproducibility; colors are color-blind-safe if the venue requires it.
