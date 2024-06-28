import cv2
import numpy as np
import openvino as ov

core = ov.Core()

class OpenvinoModel:
    """
    OpenVINO 모델을 사용하기 위한 기본 클래스
    """
    def __init__(self, model_path: str, device: str = 'CPU'):
        self.compiled_model = None
        self.input_layer = None
        self.output_layer = None
        self.height = 0
        self.width = 0

        self._init_model(model_path, device)
    
    def _init_model(self, model_path: str, device: str):
        """
        모델 초기화

        Args:
            model_path (str): 모델 경로
            device (str): 추론에 사용할 장치
        """
        model = core.read_model(model_path)
        self.compiled_model = core.compile_model(model=model, device_name=device)
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        self.height, self.width = self.input_layer.shape[2:4]
        

    def _preprocess(self, input_data: np.ndarray, transpose: bool = True) -> np.ndarray:
        """
        입력 이미지 전처리

        Args:
            input_data (np.ndarray): 입력 이미지
            transpose (bool): 이미지 transpose 여부
        
        Returns:
            np.ndarray: 전처리된 이미지
        """
        image = cv2.cvtColor(input_data, cv2.COLOR_BGR2RGB)
        input_image = cv2.resize(image, (self.width, self.height))
        if transpose:
            input_image = np.transpose(input_image, (2, 0, 1))
        input_image = np.expand_dims(input_image, axis=0)

        return input_image


class PersonDetector(OpenvinoModel):
    def __init__(self, model_path: str, device: str = 'CPU'):
        super().__init__(model_path, device)
    
    def predict(self, input_data: np.ndarray) -> np.ndarray:
        input_image = self._preprocess(input_data, transpose=True)
        results = self.compiled_model([input_image])[self.output_layer]

        height, width, _ = input_data.shape
        processed_results = self.__process_results(height, width, results)

        return processed_results
    
    def __process_results(self, h, w, results, thresh=0.5):
        # The 'results' variable is a [1, 1, N, 7] tensor.
        detections = results.reshape(-1, 7)
        boxes = []
        labels = []
        scores = []
        for i, detection in enumerate(detections):
            _, label, score, xmin, ymin, xmax, ymax = detection
            # Filter detected objects.
            if score > thresh:
                # Create a box with pixels coordinates from the box with normalized coordinates [0,1].
                boxes.append(
                    [
                        w * xmin,
                        h * ymin,
                        w * xmax,
                        h * ymax,
                    ]
                )
                labels.append(int(label))
                scores.append(float(score))

        if len(boxes) == 0:
            boxes = np.array([]).reshape(0, 4)
            scores = np.array([])
            labels = np.array([])
        return np.array(boxes), np.array(scores), np.array(labels)


class PoseEstimator(OpenvinoModel):
    def __init__(self, model_path: str, device: str = 'CPU'):
        super().__init__(model_path, device)
        self.height = 256
        self.width = 256
    
    def predict(self, input_data: np.ndarray) -> np.ndarray:
        input_image = self._preprocess(input_data, transpose=False)
        results = self.compiled_model([input_image])[self.output_layer][0]

        result_image = self.visualize(input_data, results[0])

        return result_image
    
    def visualize(self, frame, keypoints):
        height, width, _ = frame.shape
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        # canvas = frame.copy()

        threshold = 0.3
        red = (0, 0, 255)
        green = (0, 255, 0)
        blue = (255, 0, 0)
        connections = [
            (0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 5), (4, 6), # head
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),                # arms
            (5, 11), (6, 12), (11, 12),                             # body
            (11, 13), (13, 15), (12, 14), (14, 16)                  # legs
        ]
        colors = [green] * 7 + [blue] * 8 + [red] * 4

        # draw joints
        for i in range(17):
            if keypoints[i, 2] > threshold:
                pt = (int(width * keypoints[i, 1]), int(height * keypoints[i, 0]))
                cv2.circle(canvas, pt, 4, (255, 255, 255), -1)
        
        # draw lines
        for idx, (i, j) in enumerate(connections):
            if keypoints[i, 2] > threshold and keypoints[j, 2] > threshold:
                pt1 = (int(width * keypoints[i, 1]), int(height * keypoints[i, 0]))
                pt2 = (int(width * keypoints[j, 1]), int(height * keypoints[j, 0]))
                cv2.line(canvas, pt1, pt2, colors[idx], 2)

        return canvas


class PoseClassifier(OpenvinoModel):
    def __init__(self, model_path: str, device: str = 'CPU'):
        super().__init__(model_path, device)
    
    def predict(self, input_data: np.ndarray) -> tuple[int, float]:
        input_image = self._preprocess(input_data, transpose=True)
        results = self.compiled_model([input_image])[self.output_layer]
        index = np.argmax(results)
        conf = np.max(results)

        return index, conf