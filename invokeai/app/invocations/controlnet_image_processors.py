# Invocations for ControlNet image preprocessors
# initial implementation by Gregg Helt, 2023
# heavily leverages controlnet_aux package: https://github.com/patrickvonplaten/controlnet_aux
from builtins import bool, float
from typing import Dict, List, Literal, Optional, Union

import cv2
import numpy as np
from controlnet_aux import (
    CannyDetector,
    ContentShuffleDetector,
    HEDdetector,
    LeresDetector,
    LineartAnimeDetector,
    LineartDetector,
    MediapipeFaceDetector,
    MidasDetector,
    MLSDdetector,
    NormalBaeDetector,
    OpenposeDetector,
    PidiNetDetector,
    SamDetector,
    ZoeDetector,
)
from controlnet_aux.util import HWC3, ade_palette
from PIL import Image
from pydantic import BaseModel, Field, validator

from invokeai.app.invocations.primitives import ImageField, ImageOutput


from ...backend.model_management import BaseModelType
from ..models.image import ImageCategory, ResourceOrigin
from .baseinvocation import (
    BaseInvocation,
    BaseInvocationOutput,
    FieldDescriptions,
    InputField,
    Input,
    InvocationContext,
    OutputField,
    UIType,
    tags,
    title,
)


CONTROLNET_MODE_VALUES = Literal["balanced", "more_prompt", "more_control", "unbalanced"]
CONTROLNET_RESIZE_VALUES = Literal[
    "just_resize",
    "crop_resize",
    "fill_resize",
    "just_resize_simple",
]


class ControlNetModelField(BaseModel):
    """ControlNet model field"""

    model_name: str = Field(description="Name of the ControlNet model")
    base_model: BaseModelType = Field(description="Base model")


class ControlField(BaseModel):
    image: ImageField = Field(description="The control image")
    control_model: ControlNetModelField = Field(description="The ControlNet model to use")
    control_weight: Union[float, List[float]] = Field(default=1, description="The weight given to the ControlNet")
    begin_step_percent: float = Field(
        default=0, ge=0, le=1, description="When the ControlNet is first applied (% of total steps)"
    )
    end_step_percent: float = Field(
        default=1, ge=0, le=1, description="When the ControlNet is last applied (% of total steps)"
    )
    control_mode: CONTROLNET_MODE_VALUES = Field(default="balanced", description="The control mode to use")
    resize_mode: CONTROLNET_RESIZE_VALUES = Field(default="just_resize", description="The resize mode to use")

    @validator("control_weight")
    def validate_control_weight(cls, v):
        """Validate that all control weights in the valid range"""
        if isinstance(v, list):
            for i in v:
                if i < -1 or i > 2:
                    raise ValueError("Control weights must be within -1 to 2 range")
        else:
            if v < -1 or v > 2:
                raise ValueError("Control weights must be within -1 to 2 range")
        return v


class ControlOutput(BaseInvocationOutput):
    """node output for ControlNet info"""

    type: Literal["control_output"] = "control_output"

    # Outputs
    control: ControlField = OutputField(description=FieldDescriptions.control)


@title("ControlNet")
@tags("controlnet")
class ControlNetInvocation(BaseInvocation):
    """Collects ControlNet info to pass to other nodes"""

    type: Literal["controlnet"] = "controlnet"

    # Inputs
    image: ImageField = InputField(description="The control image")
    control_model: ControlNetModelField = InputField(
        default="lllyasviel/sd-controlnet-canny", description=FieldDescriptions.controlnet_model, input=Input.Direct
    )
    control_weight: Union[float, List[float]] = InputField(
        default=1.0, description="The weight given to the ControlNet", ui_type=UIType.Float
    )
    begin_step_percent: float = InputField(
        default=0, ge=-1, le=2, description="When the ControlNet is first applied (% of total steps)"
    )
    end_step_percent: float = InputField(
        default=1, ge=0, le=1, description="When the ControlNet is last applied (% of total steps)"
    )
    control_mode: CONTROLNET_MODE_VALUES = InputField(default="balanced", description="The control mode used")
    resize_mode: CONTROLNET_RESIZE_VALUES = InputField(default="just_resize", description="The resize mode used")

    def invoke(self, context: InvocationContext) -> ControlOutput:
        return ControlOutput(
            control=ControlField(
                image=self.image,
                control_model=self.control_model,
                control_weight=self.control_weight,
                begin_step_percent=self.begin_step_percent,
                end_step_percent=self.end_step_percent,
                control_mode=self.control_mode,
                resize_mode=self.resize_mode,
            ),
        )


class ImageProcessorInvocation(BaseInvocation):
    """Base class for invocations that preprocess images for ControlNet"""

    type: Literal["image_processor"] = "image_processor"

    # Inputs
    image: ImageField = InputField(description="The image to process")

    def run_processor(self, image):
        # superclass just passes through image without processing
        return image

    def invoke(self, context: InvocationContext) -> ImageOutput:
        raw_image = context.services.images.get_pil_image(self.image.image_name)
        # image type should be PIL.PngImagePlugin.PngImageFile ?
        processed_image = self.run_processor(raw_image)

        # FIXME: what happened to image metadata?
        # metadata = context.services.metadata.build_metadata(
        #     session_id=context.graph_execution_state_id, node=self
        # )

        # currently can't see processed image in node UI without a showImage node,
        #    so for now setting image_type to RESULT instead of INTERMEDIATE so will get saved in gallery
        image_dto = context.services.images.create(
            image=processed_image,
            image_origin=ResourceOrigin.INTERNAL,
            image_category=ImageCategory.CONTROL,
            session_id=context.graph_execution_state_id,
            node_id=self.id,
            is_intermediate=self.is_intermediate,
        )

        """Builds an ImageOutput and its ImageField"""
        processed_image_field = ImageField(image_name=image_dto.image_name)
        return ImageOutput(
            image=processed_image_field,
            # width=processed_image.width,
            width=image_dto.width,
            # height=processed_image.height,
            height=image_dto.height,
            # mode=processed_image.mode,
        )


@title("Canny Processor")
@tags("controlnet", "canny")
class CannyImageProcessorInvocation(ImageProcessorInvocation):
    """Canny edge detection for ControlNet"""

    type: Literal["canny_image_processor"] = "canny_image_processor"

    # Input
    low_threshold: int = InputField(
        default=100, ge=0, le=255, description="The low threshold of the Canny pixel gradient (0-255)"
    )
    high_threshold: int = InputField(
        default=200, ge=0, le=255, description="The high threshold of the Canny pixel gradient (0-255)"
    )

    def run_processor(self, image):
        canny_processor = CannyDetector()
        processed_image = canny_processor(image, self.low_threshold, self.high_threshold)
        return processed_image


@title("HED (softedge) Processor")
@tags("controlnet", "hed", "softedge")
class HedImageProcessorInvocation(ImageProcessorInvocation):
    """Applies HED edge detection to image"""

    type: Literal["hed_image_processor"] = "hed_image_processor"

    # Inputs
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)
    # safe not supported in controlnet_aux v0.0.3
    # safe: bool = InputField(default=False, description=FieldDescriptions.safe_mode)
    scribble: bool = InputField(default=False, description=FieldDescriptions.scribble_mode)

    def run_processor(self, image):
        hed_processor = HEDdetector.from_pretrained("lllyasviel/Annotators")
        processed_image = hed_processor(
            image,
            detect_resolution=self.detect_resolution,
            image_resolution=self.image_resolution,
            # safe not supported in controlnet_aux v0.0.3
            # safe=self.safe,
            scribble=self.scribble,
        )
        return processed_image


@title("Lineart Processor")
@tags("controlnet", "lineart")
class LineartImageProcessorInvocation(ImageProcessorInvocation):
    """Applies line art processing to image"""

    type: Literal["lineart_image_processor"] = "lineart_image_processor"

    # Inputs
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)
    coarse: bool = InputField(default=False, description="Whether to use coarse mode")

    def run_processor(self, image):
        lineart_processor = LineartDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = lineart_processor(
            image, detect_resolution=self.detect_resolution, image_resolution=self.image_resolution, coarse=self.coarse
        )
        return processed_image


@title("Lineart Anime Processor")
@tags("controlnet", "lineart", "anime")
class LineartAnimeImageProcessorInvocation(ImageProcessorInvocation):
    """Applies line art anime processing to image"""

    type: Literal["lineart_anime_image_processor"] = "lineart_anime_image_processor"

    # Inputs
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)

    def run_processor(self, image):
        processor = LineartAnimeDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = processor(
            image,
            detect_resolution=self.detect_resolution,
            image_resolution=self.image_resolution,
        )
        return processed_image


@title("Openpose Processor")
@tags("controlnet", "openpose", "pose")
class OpenposeImageProcessorInvocation(ImageProcessorInvocation):
    """Applies Openpose processing to image"""

    type: Literal["openpose_image_processor"] = "openpose_image_processor"

    # Inputs
    hand_and_face: bool = InputField(default=False, description="Whether to use hands and face mode")
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)

    def run_processor(self, image):
        openpose_processor = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = openpose_processor(
            image,
            detect_resolution=self.detect_resolution,
            image_resolution=self.image_resolution,
            hand_and_face=self.hand_and_face,
        )
        return processed_image


@title("Midas (Depth) Processor")
@tags("controlnet", "midas", "depth")
class MidasDepthImageProcessorInvocation(ImageProcessorInvocation):
    """Applies Midas depth processing to image"""

    type: Literal["midas_depth_image_processor"] = "midas_depth_image_processor"

    # Inputs
    a_mult: float = InputField(default=2.0, ge=0, description="Midas parameter `a_mult` (a = a_mult * PI)")
    bg_th: float = InputField(default=0.1, ge=0, description="Midas parameter `bg_th`")
    # depth_and_normal not supported in controlnet_aux v0.0.3
    # depth_and_normal: bool = InputField(default=False, description="whether to use depth and normal mode")

    def run_processor(self, image):
        midas_processor = MidasDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = midas_processor(
            image,
            a=np.pi * self.a_mult,
            bg_th=self.bg_th,
            # dept_and_normal not supported in controlnet_aux v0.0.3
            # depth_and_normal=self.depth_and_normal,
        )
        return processed_image


@title("Normal BAE Processor")
@tags("controlnet", "normal", "bae")
class NormalbaeImageProcessorInvocation(ImageProcessorInvocation):
    """Applies NormalBae processing to image"""

    type: Literal["normalbae_image_processor"] = "normalbae_image_processor"

    # Inputs
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)

    def run_processor(self, image):
        normalbae_processor = NormalBaeDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = normalbae_processor(
            image, detect_resolution=self.detect_resolution, image_resolution=self.image_resolution
        )
        return processed_image


@title("MLSD Processor")
@tags("controlnet", "mlsd")
class MlsdImageProcessorInvocation(ImageProcessorInvocation):
    """Applies MLSD processing to image"""

    type: Literal["mlsd_image_processor"] = "mlsd_image_processor"

    # Inputs
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)
    thr_v: float = InputField(default=0.1, ge=0, description="MLSD parameter `thr_v`")
    thr_d: float = InputField(default=0.1, ge=0, description="MLSD parameter `thr_d`")

    def run_processor(self, image):
        mlsd_processor = MLSDdetector.from_pretrained("lllyasviel/Annotators")
        processed_image = mlsd_processor(
            image,
            detect_resolution=self.detect_resolution,
            image_resolution=self.image_resolution,
            thr_v=self.thr_v,
            thr_d=self.thr_d,
        )
        return processed_image


@title("PIDI Processor")
@tags("controlnet", "pidi")
class PidiImageProcessorInvocation(ImageProcessorInvocation):
    """Applies PIDI processing to image"""

    type: Literal["pidi_image_processor"] = "pidi_image_processor"

    # Inputs
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)
    safe: bool = InputField(default=False, description=FieldDescriptions.safe_mode)
    scribble: bool = InputField(default=False, description=FieldDescriptions.scribble_mode)

    def run_processor(self, image):
        pidi_processor = PidiNetDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = pidi_processor(
            image,
            detect_resolution=self.detect_resolution,
            image_resolution=self.image_resolution,
            safe=self.safe,
            scribble=self.scribble,
        )
        return processed_image


@title("Content Shuffle Processor")
@tags("controlnet", "contentshuffle")
class ContentShuffleImageProcessorInvocation(ImageProcessorInvocation):
    """Applies content shuffle processing to image"""

    type: Literal["content_shuffle_image_processor"] = "content_shuffle_image_processor"

    # Inputs
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)
    h: Optional[int] = InputField(default=512, ge=0, description="Content shuffle `h` parameter")
    w: Optional[int] = InputField(default=512, ge=0, description="Content shuffle `w` parameter")
    f: Optional[int] = InputField(default=256, ge=0, description="Content shuffle `f` parameter")

    def run_processor(self, image):
        content_shuffle_processor = ContentShuffleDetector()
        processed_image = content_shuffle_processor(
            image,
            detect_resolution=self.detect_resolution,
            image_resolution=self.image_resolution,
            h=self.h,
            w=self.w,
            f=self.f,
        )
        return processed_image


# should work with controlnet_aux >= 0.0.4 and timm <= 0.6.13
@title("Zoe (Depth) Processor")
@tags("controlnet", "zoe", "depth")
class ZoeDepthImageProcessorInvocation(ImageProcessorInvocation):
    """Applies Zoe depth processing to image"""

    type: Literal["zoe_depth_image_processor"] = "zoe_depth_image_processor"

    def run_processor(self, image):
        zoe_depth_processor = ZoeDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = zoe_depth_processor(image)
        return processed_image


@title("Mediapipe Face Processor")
@tags("controlnet", "mediapipe", "face")
class MediapipeFaceProcessorInvocation(ImageProcessorInvocation):
    """Applies mediapipe face processing to image"""

    type: Literal["mediapipe_face_processor"] = "mediapipe_face_processor"

    # Inputs
    max_faces: int = InputField(default=1, ge=1, description="Maximum number of faces to detect")
    min_confidence: float = InputField(default=0.5, ge=0, le=1, description="Minimum confidence for face detection")

    def run_processor(self, image):
        # MediaPipeFaceDetector throws an error if image has alpha channel
        #     so convert to RGB if needed
        if image.mode == "RGBA":
            image = image.convert("RGB")
        mediapipe_face_processor = MediapipeFaceDetector()
        processed_image = mediapipe_face_processor(image, max_faces=self.max_faces, min_confidence=self.min_confidence)
        return processed_image


@title("Leres (Depth) Processor")
@tags("controlnet", "leres", "depth")
class LeresImageProcessorInvocation(ImageProcessorInvocation):
    """Applies leres processing to image"""

    type: Literal["leres_image_processor"] = "leres_image_processor"

    # Inputs
    thr_a: float = InputField(default=0, description="Leres parameter `thr_a`")
    thr_b: float = InputField(default=0, description="Leres parameter `thr_b`")
    boost: bool = InputField(default=False, description="Whether to use boost mode")
    detect_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.detect_res)
    image_resolution: int = InputField(default=512, ge=0, description=FieldDescriptions.image_res)

    def run_processor(self, image):
        leres_processor = LeresDetector.from_pretrained("lllyasviel/Annotators")
        processed_image = leres_processor(
            image,
            thr_a=self.thr_a,
            thr_b=self.thr_b,
            boost=self.boost,
            detect_resolution=self.detect_resolution,
            image_resolution=self.image_resolution,
        )
        return processed_image


@title("Tile Resample Processor")
@tags("controlnet", "tile")
class TileResamplerProcessorInvocation(ImageProcessorInvocation):
    """Tile resampler processor"""

    type: Literal["tile_image_processor"] = "tile_image_processor"

    # Inputs
    # res: int = InputField(default=512, ge=0, le=1024, description="The pixel resolution for each tile")
    down_sampling_rate: float = InputField(default=1.0, ge=1.0, le=8.0, description="Down sampling rate")

    # tile_resample copied from sd-webui-controlnet/scripts/processor.py
    def tile_resample(
        self,
        np_img: np.ndarray,
        res=512,  # never used?
        down_sampling_rate=1.0,
    ):
        np_img = HWC3(np_img)
        if down_sampling_rate < 1.1:
            return np_img
        H, W, C = np_img.shape
        H = int(float(H) / float(down_sampling_rate))
        W = int(float(W) / float(down_sampling_rate))
        np_img = cv2.resize(np_img, (W, H), interpolation=cv2.INTER_AREA)
        return np_img

    def run_processor(self, img):
        np_img = np.array(img, dtype=np.uint8)
        processed_np_image = self.tile_resample(
            np_img,
            # res=self.tile_size,
            down_sampling_rate=self.down_sampling_rate,
        )
        processed_image = Image.fromarray(processed_np_image)
        return processed_image


@title("Segment Anything Processor")
@tags("controlnet", "segmentanything")
class SegmentAnythingProcessorInvocation(ImageProcessorInvocation):
    """Applies segment anything processing to image"""

    type: Literal["segment_anything_processor"] = "segment_anything_processor"

    def run_processor(self, image):
        # segment_anything_processor = SamDetector.from_pretrained("ybelkada/segment-anything", subfolder="checkpoints")
        segment_anything_processor = SamDetectorReproducibleColors.from_pretrained(
            "ybelkada/segment-anything", subfolder="checkpoints"
        )
        np_img = np.array(image, dtype=np.uint8)
        processed_image = segment_anything_processor(np_img)
        return processed_image


class SamDetectorReproducibleColors(SamDetector):
    # overriding SamDetector.show_anns() method to use reproducible colors for segmentation image
    #     base class show_anns() method randomizes colors,
    #     which seems to also lead to non-reproducible image generation
    # so using ADE20k color palette instead
    def show_anns(self, anns: List[Dict]):
        if len(anns) == 0:
            return
        sorted_anns = sorted(anns, key=(lambda x: x["area"]), reverse=True)
        h, w = anns[0]["segmentation"].shape
        final_img = Image.fromarray(np.zeros((h, w, 3), dtype=np.uint8), mode="RGB")
        palette = ade_palette()
        for i, ann in enumerate(sorted_anns):
            m = ann["segmentation"]
            img = np.empty((m.shape[0], m.shape[1], 3), dtype=np.uint8)
            # doing modulo just in case number of annotated regions exceeds number of colors in palette
            ann_color = palette[i % len(palette)]
            img[:, :] = ann_color
            final_img.paste(Image.fromarray(img, mode="RGB"), (0, 0), Image.fromarray(np.uint8(m * 255)))
        return np.array(final_img, dtype=np.uint8)
