"""
model_zoo.py — Ready-to-run PlotNeuralNet generators for STANDARD architectures.

Each `build_<model>()` returns an `arch` list (the PlotNeuralNet way). Run any
of them from a `pyexamples/`-style directory where `pycore` is importable, and
where `pnn_ext.py` sits alongside.

    python model_zoo.py lenet        # writes lenet.tex
    python model_zoo.py alexnet      # writes alexnet.tex
    python model_zoo.py vgg16
    python model_zoo.py resnet
    python model_zoo.py unet
    python model_zoo.py encoder_decoder
    python model_zoo.py vit
    python model_zoo.py autoencoder

then:  pdflatex <name>.tex     (or: bash ../tikzmake.sh <name>)

Models included (the "standard" set used in most papers/talks):
  - lenet            classic 2-conv CNN
  - alexnet          5-conv + 3-FC
  - vgg16            block-structured deep CNN (encoder)
  - resnet           residual blocks with skip arcs
  - unet             encoder-decoder with copy/skip connections (segmentation)
  - encoder_decoder  generic enc-dec (e.g. for medical registration / SegNet)
  - vit              Vision Transformer (patch embed + transformer stack)
  - autoencoder      symmetric AE / VAE-style bottleneck

These cover CNNs (classification + segmentation), residual nets, transformers,
and generative/representation models — enough to illustrate almost any DL paper.

Author note: sizes follow the convention "halve H/D at each downsample, grow
width with channels" so the figures read like real networks. Tune freely.
"""

import sys
sys.path.append('../')                      # pycore importable from pyexamples/
from pycore.tikzeng import *                 # upstream primitives
try:
    from pycore.blocks import *              # block_2ConvPool, block_Unconv, block_Res
    HAVE_BLOCKS = True
except Exception:
    HAVE_BLOCKS = False
from pnn_ext import *                         # our extensions


# ===========================================================================
# 1. LeNet-style
# ===========================================================================
def build_lenet():
    return [
        to_head('..'), to_cor(), extra_colors(), to_begin(),
        to_Conv("c1", 32, 6, offset="(0,0,0)", to="(0,0,0)", height=32, depth=32, width=2, caption="Conv1"),
        to_Pool("p1", offset="(0,0,0)", to="(c1-east)", height=24, depth=24, width=1),
        to_Conv("c2", 14, 16, offset="(1.5,0,0)", to="(p1-east)", height=20, depth=20, width=3, caption="Conv2"),
        to_connection("p1", "c2"),
        to_Pool("p2", offset="(0,0,0)", to="(c2-east)", height=14, depth=14, width=1),
        to_FC("f1", 120, offset="(2,0,0)", to="(p2-east)", caption="FC120"),
        to_connection("p2", "f1"),
        to_FC("f2", 84, offset="(1,0,0)", to="(f1-east)", caption="FC84"),
        to_connection("f1", "f2"),
        to_SoftMax("sm", 10, offset="(1.5,0,0)", to="(f2-east)", caption="SOFT"),
        to_connection("f2", "sm"),
        to_end(),
    ]


# ===========================================================================
# 2. AlexNet
# ===========================================================================
def build_alexnet():
    return [
        to_head('..'), to_cor(), extra_colors(), to_begin(),
        to_Conv("c1", 227, 96, offset="(0,0,0)", to="(0,0,0)", height=55, depth=55, width=3, caption="Conv1"),
        to_Pool("p1", offset="(0,0,0)", to="(c1-east)", height=40, depth=40, width=2),
        to_Conv("c2", 27, 256, offset="(1.5,0,0)", to="(p1-east)", height=40, depth=40, width=4, caption="Conv2"),
        to_connection("p1", "c2"),
        to_Pool("p2", offset="(0,0,0)", to="(c2-east)", height=30, depth=30, width=2),
        to_Conv("c3", 13, 384, offset="(1.5,0,0)", to="(p2-east)", height=30, depth=30, width=5, caption="Conv3"),
        to_connection("p2", "c3"),
        to_Conv("c4", 13, 384, offset="(0.6,0,0)", to="(c3-east)", height=30, depth=30, width=5, caption="Conv4"),
        to_Conv("c5", 13, 256, offset="(0.6,0,0)", to="(c4-east)", height=30, depth=30, width=4, caption="Conv5"),
        to_Pool("p5", offset="(0,0,0)", to="(c5-east)", height=20, depth=20, width=2),
        to_FC("f6", 4096, offset="(2,0,0)", to="(p5-east)", caption="FC6"),
        to_connection("p5", "f6"),
        to_FC("f7", 4096, offset="(1,0,0)", to="(f6-east)", caption="FC7"),
        to_connection("f6", "f7"),
        to_SoftMax("sm", 1000, offset="(1.5,0,0)", to="(f7-east)", caption="SOFT"),
        to_connection("f7", "sm"),
        to_end(),
    ]


# ===========================================================================
# 3. VGG-16 (block structured). Uses block_2ConvPool if available.
# ===========================================================================
def build_vgg16():
    head = [to_head('..'), to_cor(), extra_colors(), to_begin(),
            to_input('../examples/fcn8s/cats.jpg', name='img'),
            # A real Box named 'input' so 'input-east' is a valid anchor for the
            # first block. (A plain \node image has no -east anchor; connecting a
            # block straight from the image fails: "No shape named input-east".)
            to_Conv("input", 224, 3, offset="(0,0,0)", to="(0,0,0)", height=40, depth=40, width=1, caption="Input")]
    if HAVE_BLOCKS:
        body = [
            *block_2ConvPool(name='b1', botton='input', top='p1', s_filer=224, n_filer=64,  offset="(1,0,0)", size=(40,40,1.5)),
            *block_2ConvPool(name='b2', botton='p1',    top='p2', s_filer=112, n_filer=128, offset="(1,0,0)", size=(32,32,2.0)),
            *block_2ConvPool(name='b3', botton='p2',    top='p3', s_filer=56,  n_filer=256, offset="(1,0,0)", size=(25,25,3.0)),
            *block_2ConvPool(name='b4', botton='p3',    top='p4', s_filer=28,  n_filer=512, offset="(1,0,0)", size=(16,16,4.0)),
            *block_2ConvPool(name='b5', botton='p4',    top='p5', s_filer=14,  n_filer=512, offset="(1,0,0)", size=(10,10,4.0)),
        ]
        last = "p5"
    else:
        # Fallback without blocks.py: manual conv/pool chain.
        body, last = [], "0,0,0"
        specs = [(224,64,40,1.5),(112,128,32,2.0),(56,256,25,3.0),(28,512,16,4.0),(14,512,10,4.0)]
        prev = "(0,0,0)"
        for i,(s,n,h,w) in enumerate(specs,1):
            cname=f"c{i}"; pname=f"p{i}"
            body.append(to_Conv(cname, s, n, offset="(1,0,0)" if i>1 else "(0,0,0)", to=prev, height=h, depth=h, width=w, caption=f"Conv{i}"))
            if i>1: body.append(to_connection(last, cname))
            body.append(to_Pool(pname, offset="(0,0,0)", to=f"({cname}-east)", height=max(h-6,6), depth=max(h-6,6), width=1))
            prev=f"({pname}-east)"; last=pname
    tail = [
        to_FC("f6", 4096, offset="(2,0,0)", to=f"({last}-east)", caption="FC"),
        to_connection(last, "f6"),
        to_SoftMax("sm", 1000, offset="(1.5,0,0)", to="(f6-east)", caption="SOFT"),
        to_connection("f6", "sm"),
        to_end(),
    ]
    return head + body + tail


# ===========================================================================
# 4. ResNet (residual blocks with skip arcs). Uses block_Res if available.
# ===========================================================================
def build_resnet():
    arch = [to_head('..'), to_cor(), extra_colors(), to_begin(),
            to_Conv("c1", 112, 64, offset="(0,0,0)", to="(0,0,0)", height=40, depth=40, width=2, caption="Conv 7x7"),
            to_Pool("p1", offset="(0,0,0)", to="(c1-east)", height=32, depth=32, width=1)]
    if HAVE_BLOCKS:
        arch += [
            *block_Res(num=2, name="r1", botton="p1",     top="r1_end", s_filer=56, n_filer=64,  offset="(1.5,0,0)", size=(32,32,2.0)),
            *block_Res(num=2, name="r2", botton="r1_end", top="r2_end", s_filer=28, n_filer=128, offset="(2,0,0)",   size=(25,25,2.5)),
            *block_Res(num=2, name="r3", botton="r2_end", top="r3_end", s_filer=14, n_filer=256, offset="(2,0,0)",   size=(16,16,3.0)),
        ]
        last = "r3_end"
    else:
        # Manual two-conv residual block with an explicit skip arc.
        arch += [
            to_Conv("ra", 56, 64, offset="(1.5,0,0)", to="(p1-east)", height=32, depth=32, width=2, caption="Conv"),
            to_connection("p1", "ra"),
            to_Conv("rb", 56, 64, offset="(0.8,0,0)", to="(ra-east)", height=32, depth=32, width=2, caption="Conv"),
            to_skip(of="ra", to="rb", pos=1.5),
        ]
        last = "rb"
    arch += [
        to_GAP("gap", offset="(2,0,0)", to=f"({last}-east)", caption="GAP"),
        to_connection(last, "gap"),
        to_SoftMax("sm", 1000, offset="(1.5,0,0)", to="(gap-east)", caption="SOFT"),
        to_connection("gap", "sm"),
        to_end(),
    ]
    return arch


# ===========================================================================
# 5. U-Net (encoder-decoder + copy/skip). Uses block_2ConvPool + block_Unconv.
# ===========================================================================
def build_unet():
    if not HAVE_BLOCKS:
        # Minimal manual enc-dec fallback (no internal block node names to skip).
        return build_encoder_decoder()
    return [
        to_head('..'), to_cor(), extra_colors(), to_begin(),
        to_input('../examples/fcn8s/cats.jpg', name='img'),
        to_Conv("input", 512, 3, offset="(0,0,0)", to="(0,0,0)", height=32, depth=32, width=1, caption="Input"),
        # Encoder
        *block_2ConvPool(name='b1', botton='input', top='p1', s_filer=512, n_filer=64,  offset="(1,0,0)", size=(32,32,2.5)),
        *block_2ConvPool(name='b2', botton='p1',    top='p2', s_filer=256, n_filer=128, offset="(1,0,0)", size=(25,25,3.0)),
        *block_2ConvPool(name='b3', botton='p2',    top='p3', s_filer=128, n_filer=256, offset="(1,0,0)", size=(16,16,4.0)),
        # Bottleneck
        to_ConvConvRelu("bn", 64, (512,512), offset="(2,0,0)", to="(p3-east)", width=(8,8), height=8, depth=8, caption="Bottleneck"),
        to_connection("p3", "bn"),
        # Decoder (mirror)
        *block_Unconv(name='b5', botton='bn',   top='end5', s_filer=128, n_filer=256, offset="(2.1,0,0)", size=(16,16,4.0)),
        *block_Unconv(name='b6', botton='end5', top='end6', s_filer=256, n_filer=128, offset="(2.1,0,0)", size=(25,25,3.0)),
        *block_Unconv(name='b7', botton='end6', top='end7', s_filer=512, n_filer=64,  offset="(2.1,0,0)", size=(32,32,2.5)),
        # Output
        to_ConvSoftMax("sm", 512, offset="(0.75,0,0)", to="(end7-east)", width=1, height=32, depth=32, caption="Output"),
        to_connection("end7", "sm"),
        # Skip (copy) connections encoder -> decoder. Node names follow blocks.py
        # convention: ccr_<name> (encoder convs) and ccr_res_<name> (decoder).
        to_skip(of='ccr_b1', to='ccr_res_b7', pos=1.5),
        to_skip(of='ccr_b2', to='ccr_res_b6', pos=1.5),
        to_skip(of='ccr_b3', to='ccr_res_b5', pos=1.5),
        to_end(),
    ]


# ===========================================================================
# 6. Generic encoder-decoder (SegNet-like / medical registration backbone)
# ===========================================================================
def build_encoder_decoder():
    return [
        to_head('..'), to_cor(), extra_colors(), to_begin(),
        to_input('../examples/fcn8s/cats.jpg', name='input'),
        # Encoder
        to_Conv("e1", 256, 64,  offset="(0,0,0)",  to="(0,0,0)",   height=40, depth=40, width=2, caption="Enc1"),
        to_Pool("ep1", offset="(0,0,0)", to="(e1-east)", height=30, depth=30, width=1),
        to_Conv("e2", 128, 128, offset="(1.2,0,0)", to="(ep1-east)", height=30, depth=30, width=3, caption="Enc2"),
        to_connection("ep1", "e2"),
        to_Pool("ep2", offset="(0,0,0)", to="(e2-east)", height=20, depth=20, width=1),
        to_Conv("e3", 64, 256,  offset="(1.2,0,0)", to="(ep2-east)", height=20, depth=20, width=4, caption="Enc3"),
        to_connection("ep2", "e3"),
        # Bottleneck
        to_Conv("bn", 32, 512,  offset="(1.5,0,0)", to="(e3-east)",  height=12, depth=12, width=5, caption="Bottleneck"),
        to_connection("e3", "bn"),
        # Decoder
        to_UnPool("up1", offset="(1.5,0,0)", to="(bn-east)", height=20, depth=20, width=1),
        to_connection("bn", "up1"),
        to_Conv("d1", 64, 256,  offset="(0,0,0)", to="(up1-east)", height=20, depth=20, width=4, caption="Dec1"),
        to_UnPool("up2", offset="(1.2,0,0)", to="(d1-east)", height=30, depth=30, width=1),
        to_connection("d1", "up2"),
        to_Conv("d2", 128, 128, offset="(0,0,0)", to="(up2-east)", height=30, depth=30, width=3, caption="Dec2"),
        to_UnPool("up3", offset="(1.2,0,0)", to="(d2-east)", height=40, depth=40, width=1),
        to_connection("d2", "up3"),
        to_Conv("d3", 256, 64,  offset="(0,0,0)", to="(up3-east)", height=40, depth=40, width=2, caption="Dec3"),
        to_ConvSoftMax("sm", 256, offset="(1.2,0,0)", to="(d3-east)", width=1, height=40, depth=40, caption="Output"),
        to_connection("d3", "sm"),
        to_end(),
    ]


# ===========================================================================
# 7. Vision Transformer (ViT): patch embed -> transformer stack -> head
# ===========================================================================
def build_vit():
    arch = [
        to_head('..'), to_cor(), extra_colors(), to_begin(),
        to_input('../examples/fcn8s/cats.jpg', name='input'),
        to_Embedding("emb", offset="(0,0,0)", to="(0,0,0)", caption="PatchEmbed", dim=768, height=40, depth=40),
    ]
    prev = "emb"
    for i in range(1, 5):                       # show 4 of N transformer blocks
        name = f"t{i}"
        off = "(1.2,0,0)" if i == 1 else "(0.8,0,0)"
        arch.append(to_Transformer(name, offset=off, to=f"({prev}-east)",
                                   height=40, depth=40, width=3,
                                   caption=f"Block {i}", dim=768))
        if i == 1:
            arch.append(to_connection("emb", name))
        prev = name
    arch += [
        to_GAP("cls", offset="(1.5,0,0)", to=f"({prev}-east)", caption="CLS/GAP"),
        to_connection(prev, "cls"),
        to_FC("head", 1000, offset="(1.2,0,0)", to="(cls-east)", caption="MLP Head"),
        to_connection("cls", "head"),
        to_SoftMax("sm", 1000, offset="(1.2,0,0)", to="(head-east)", caption="SOFT"),
        to_connection("head", "sm"),
        to_end(),
    ]
    return arch


# ===========================================================================
# 8. Autoencoder / VAE-style symmetric bottleneck
# ===========================================================================
def build_autoencoder():
    return [
        to_head('..'), to_cor(), extra_colors(), to_begin(),
        to_input('../examples/fcn8s/cats.jpg', name='input'),
        to_Conv("e1", 256, 32,  offset="(0,0,0)",  to="(0,0,0)",   height=40, depth=40, width=2, caption="Enc"),
        to_Pool("ep1", offset="(0,0,0)", to="(e1-east)", height=30, depth=30, width=1),
        to_Conv("e2", 128, 64,  offset="(1.2,0,0)", to="(ep1-east)", height=30, depth=30, width=3, caption="Enc"),
        to_connection("ep1", "e2"),
        to_Pool("ep2", offset="(0,0,0)", to="(e2-east)", height=20, depth=20, width=1),
        # Latent code (thin tall box)
        to_FC("z", 256, offset="(1.5,0,0)", to="(ep2-east)", height=4, depth=30, width=1, caption="z (latent)"),
        to_connection("ep2", "z"),
        # Decoder mirror
        to_UnPool("up1", offset="(1.5,0,0)", to="(z-east)", height=20, depth=20, width=1),
        to_connection("z", "up1"),
        to_Conv("d1", 128, 64,  offset="(0,0,0)", to="(up1-east)", height=30, depth=30, width=3, caption="Dec"),
        to_UnPool("up2", offset="(1.2,0,0)", to="(d1-east)", height=40, depth=40, width=1),
        to_connection("d1", "up2"),
        to_Conv("d2", 256, 32,  offset="(0,0,0)", to="(up2-east)", height=40, depth=40, width=2, caption="Dec"),
        to_Conv("out", 256, 3,  offset="(1.2,0,0)", to="(d2-east)", height=40, depth=40, width=1, caption="Recon"),
        to_connection("d2", "out"),
        to_end(),
    ]


# ===========================================================================
# Dispatcher
# ===========================================================================
MODELS = {
    "lenet": build_lenet,
    "alexnet": build_alexnet,
    "vgg16": build_vgg16,
    "resnet": build_resnet,
    "unet": build_unet,
    "encoder_decoder": build_encoder_decoder,
    "vit": build_vit,
    "autoencoder": build_autoencoder,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MODELS:
        print("Usage: python model_zoo.py <model>")
        print("Models:", ", ".join(MODELS))
        sys.exit(1)
    name = sys.argv[1]
    arch = MODELS[name]()
    to_generate(arch, name + ".tex")
    print(f"Wrote {name}.tex  ->  compile with: pdflatex {name}.tex")


if __name__ == "__main__":
    main()
