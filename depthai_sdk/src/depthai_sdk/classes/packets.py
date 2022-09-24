from typing import Tuple, List, Union
import depthai as dai
import numpy as np

class Detection():
    def __init__(self):
        pass

    # Original ImgDetection
    imgDetection: dai.ImgDetection
    label_str: str
    color: Tuple[int,int,int]
    # Normalized bounding box
    topLeft: Tuple[int,int]
    bottomRight: Tuple[int, int]


class TwoStageDetection(Detection):
    def __init__(self):
        super().__init__()

    nn_data: dai.NNData


class FramePacket:
    name: str  # ImgFrame stream name
    imgFrame: dai.ImgFrame  # Original depthai message
    frame: np.ndarray  # cv2 frame for visualization
    def __init__(self, name: str, imgFrame: dai.ImgFrame, frame: np.ndarray):
        self.name = name
        self.imgFrame = imgFrame
        self.frame = frame


class SpatialBbMappingPacket(FramePacket):
    config: dai.SpatialLocationCalculatorConfig

    def __init__(self, name: str, imgFrame: dai.ImgFrame, config: dai.SpatialLocationCalculatorConfig):
        super().__init__(name, imgFrame, imgFrame.getFrame())
        self.config = config


class DetectionPacket(FramePacket):
    # Original depthai messages
    imgDetections: Union[dai.ImgDetections, dai.SpatialImgDetections]
    detections: List[Detection]

    def __init__(self,
                 name: str,
                 imgFrame: dai.ImgFrame,
                 imgDetections: Union[dai.ImgDetections, dai.SpatialImgDetections]):
        super().__init__(name, imgFrame,  imgFrame.getCvFrame())
        self.imgDetections = imgDetections
        self.detections = []

    def isSpatialDetection(self) -> bool:
        return isinstance(self.imgDetections, dai.SpatialImgDetections)

    def add_detection(self, img_det: dai.ImgDetection, bbox: np.ndarray, txt:str, color):
        det = Detection()
        det.imgDetection = img_det
        det.label_str = txt
        det.color = color
        det.topLeft = (bbox[0], bbox[1])
        det.bottomRight = (bbox[2], bbox[3])
        self.detections.append(det)


class TwoStagePacket(DetectionPacket):
    # Original depthai messages
    nnData: List[dai.NNData]
    labels: List[int] = None
    _cntr: int = 0 # Label counter

    def __init__(self, name: str,
                 imgFrame: dai.ImgFrame,
                 imgDetections: dai.ImgDetections,
                 nnData: List[dai.NNData],
                 labels: List[int]):
        super().__init__(name, imgFrame, imgDetections)
        self.frame = self.imgFrame.getCvFrame()
        self.nnData = nnData
        self.labels = labels
        self._cntr = 0

    def isSpatialDetection(self) -> bool:
        return isinstance(self.imgDetections, dai.SpatialImgDetections)

    def add_detection(self, img_det: dai.ImgDetection, bbox: np.ndarray, txt:str, color):
        det = TwoStageDetection()
        det.imgDetection = img_det
        det.color = color
        det.topLeft = (bbox[0], bbox[1])
        det.bottomRight = (bbox[2], bbox[3])

        # Append the second stage NN result to the detection
        if self.labels is None or img_det.label in self.labels:
            print(self._cntr, self.nnData, len(self.imgDetections.detections))
            det.nn_data = self.nnData[self._cntr]
            self._cntr += 1

        self.detections.append(det)

