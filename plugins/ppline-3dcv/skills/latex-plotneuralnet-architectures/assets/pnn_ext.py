"""
pnn_ext.py — Extension helpers for PlotNeuralNet (HarisIqbal88).

This module sits ON TOP of the upstream `pycore/tikzeng.py` and adds:
  * modern layer types the original lacks (BatchNorm, Dropout, FC, GAP,
    Attention/Transformer block, Concat junction, generic labelled Box);
  * small utilities for auto-chaining layers and for embedding captions
    with channel / resolution labels consistently.

It emits the SAME kind of TikZ strings as the upstream `to_*` functions, so
returned strings drop straight into an `arch = [...]` list and are written by
`to_generate(...)`. Nothing here requires editing the upstream repo.

USAGE
-----
Place this file next to your generator script (or anywhere importable) and:

    import sys; sys.path.append('../')          # so pycore is importable
    from pycore.tikzeng import *                 # upstream primitives
    from pnn_ext import *                        # these extensions

    arch = [
        to_head('..'), to_cor(), extra_colors(), to_begin(),
        to_Conv("c1", 224, 64, offset="(0,0,0)", to="(0,0,0)", height=40, depth=40, width=2),
        to_BatchNorm("bn1", to="(c1-east)"),
        to_Dropout("do1", to="(bn1-east)"),
        to_end(),
    ]

Compile with the repo's `bash ../tikzmake.sh <name>` (pdflatex + standalone).

Tested against PlotNeuralNet master (pic styles Box / RightBandedBox / Ball,
init.tex colors). The strings use only TikZ primitives + the Box pic, so they
render with the stock layer .sty files.
"""

# --------------------------------------------------------------------------- #
# Extra colors. Append the returned string to `arch` right after to_cor().
# (Defining new \Color macros that the helpers below reference.)
# --------------------------------------------------------------------------- #
def extra_colors():
    return r"""
\def\BnColor{rgb:green,3;black,1}
\def\DropoutColor{rgb:black,2;white,5}
\def\FcColorX{rgb:blue,5;red,2.5;white,5}
\def\AttnColor{rgb:magenta,4;blue,3;white,6}
\def\TransColor{rgb:orange,5;yellow,2;white,5}
\def\GapColor{rgb:cyan,4;blue,2;white,6}
\def\ConcatColor{rgb:green,5;blue,3}
"""


# --------------------------------------------------------------------------- #
# Generic labelled box. All the specific helpers below delegate to this.
# Mirrors the upstream to_Conv string shape but with arbitrary fill + caption.
# --------------------------------------------------------------------------- #
def to_LayerBox(name, fill="\\ConvColor", offset="(0,0,0)", to="(0,0,0)",
                width=1, height=40, depth=40, caption=" ",
                xlabel=" ", zlabel=" ", opacity=0.7):
    return r"""
\pic[shift={""" + offset + r"""}] at """ + to + r"""
    {Box={
        name=""" + name + r""",
        caption=""" + caption + r""",
        xlabel={{""" + str(xlabel) + r""", }},
        zlabel=""" + str(zlabel) + r""",
        fill=""" + fill + r""",
        opacity=""" + str(opacity) + r""",
        height=""" + str(height) + r""",
        width=""" + str(width) + r""",
        depth=""" + str(depth) + r"""
        }
    };
"""


# --------------------------------------------------------------------------- #
# Modern layer types
# --------------------------------------------------------------------------- #
def to_BatchNorm(name, offset="(0,0,0)", to="(0,0,0)",
                 width=1, height=40, depth=40, caption="BN"):
    """Thin slab representing a normalization layer (BN / LN / GN)."""
    return to_LayerBox(name, fill="\\BnColor", offset=offset, to=to,
                       width=width, height=height, depth=depth,
                       caption=caption, opacity=0.8)


def to_Dropout(name, offset="(0,0,0)", to="(0,0,0)",
               width=1, height=40, depth=40, caption="Drop"):
    """Faint slab for dropout / stochastic regularization."""
    return to_LayerBox(name, fill="\\DropoutColor", offset=offset, to=to,
                       width=width, height=height, depth=depth,
                       caption=caption, opacity=0.5)


def to_FC(name, n=4096, offset="(0,0,0)", to="(0,0,0)",
          width=1, height=3, depth=40, caption="FC"):
    """Fully-connected / dense layer (tall thin box). n -> zlabel (#units)."""
    return to_LayerBox(name, fill="\\FcColorX", offset=offset, to=to,
                       width=width, height=height, depth=depth,
                       caption=caption, zlabel=n, opacity=0.8)


def to_GAP(name, offset="(0,0,0)", to="(0,0,0)",
           width=1, height=8, depth=8, caption="GAP"):
    """Global average pooling: collapses spatial dims to a vector."""
    return to_LayerBox(name, fill="\\GapColor", offset=offset, to=to,
                       width=width, height=height, depth=depth,
                       caption=caption, opacity=0.7)


def to_Attention(name, offset="(0,0,0)", to="(0,0,0)",
                 width=2, height=40, depth=40, caption="MHSA", heads=8):
    """Multi-head self-attention block."""
    return to_LayerBox(name, fill="\\AttnColor", offset=offset, to=to,
                       width=width, height=height, depth=depth,
                       caption=caption, xlabel=str(heads) + "h", opacity=0.75)


def to_Transformer(name, offset="(0,0,0)", to="(0,0,0)",
                   width=3, height=40, depth=40, caption="Transformer",
                   dim=768):
    """Transformer encoder block (MHSA + MLP + norms folded into one box)."""
    return to_LayerBox(name, fill="\\TransColor", offset=offset, to=to,
                       width=width, height=height, depth=depth,
                       caption=caption, xlabel=dim, opacity=0.75)


def to_Concat(name, offset="(0,0,0)", to="(0,0,0)", radius=2.0, opacity=0.6):
    """Concatenation / merge junction, drawn as a small ball (like to_Sum)."""
    return r"""
\pic[shift={""" + offset + r"""}] at """ + to + r"""
    {Ball={
        name=""" + name + r""",
        fill=\ConcatColor,
        opacity=""" + str(opacity) + r""",
        radius=""" + str(radius) + r""",
        logo=$\|$
        }
    };
"""


def to_Embedding(name, offset="(0,0,0)", to="(0,0,0)",
                 width=1.5, height=3, depth=40, caption="Embed", dim=768):
    """Token / patch embedding layer feeding a transformer."""
    return to_LayerBox(name, fill="\\TransColor", offset=offset, to=to,
                       width=width, height=height, depth=depth,
                       caption=caption, zlabel=dim, opacity=0.8)


# --------------------------------------------------------------------------- #
# Chaining utilities — reduce boilerplate for long sequential stacks.
# --------------------------------------------------------------------------- #
def chain(*pieces):
    """Flatten a mix of strings and lists (from block_* helpers) into one list.

        arch = [to_head('..'), to_cor(), to_begin(),
                *chain(stage1, stage2, [to_end()])]
    """
    out = []
    for p in pieces:
        if isinstance(p, (list, tuple)):
            out.extend(p)
        else:
            out.append(p)
    return out


def conv_bn_relu(name, s_filer, n_filer, to, offset="(1,0,0)",
                 height=40, depth=40, width=2):
    """Common Conv->BN->ReLU motif as a 2-element list (conv box + BN slab +
    a connection). Returns a list to splice with `*`.

    Note: requires the upstream to_Conv / to_connection in scope.
    """
    conv = to_Conv(name, s_filer, n_filer, offset=offset, to=to,
                   height=height, depth=depth, width=width, caption="Conv")
    bn = to_BatchNorm(name + "_bn", to="(" + name + "-east)",
                      height=height, depth=depth, width=1)
    return [conv, bn]
