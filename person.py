class Person:
    def __init__(self, name) -> None:
        self.name = name
        self.fname = ''
        self.imgs = []

    def add_img(self, img):
        self.imgs.append(img)


class FImage:
    def __init__(self, path, face_paths) -> None:
        self.path = path
        self.face_paths = face_paths

    def add_face_path(self, face_path):
        self.face_paths.append(face_path)
