import uuid

class CosmosPageObj:
    def __init__(self, 
                 page_number: int,
                 content: str, 
                 content_vector, 
                 keywords: str, 
                 file_name: str, 
                 file_path: str, 
                 detele_flag: bool = False, 
                 is_contain_image: bool = False, 
                 image_blob_path: str = None, 
                ):
        self.id = str(uuid.uuid4())
        self.page_number = page_number
        self.content = content
        self.content_vector = content_vector
        self.keywords = keywords
        self.file_name = file_name
        self.file_path = file_path
        self.detele_flag = detele_flag
        self.is_contain_image = is_contain_image
        self.image_blob_path = image_blob_path

    def to_dict(self):
        return {
            "id": self.id,
            "page_number": self.page_number,
            "content": self.content,
            "content_vector": self.content_vector,
            "keywords": self.keywords,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "detele_flag": self.detele_flag,
            "is_contain_image": self.is_contain_image,
            "image_blob_path": self.image_blob_path,
        }
    
    @staticmethod
    def from_dict(dict):
        return CosmosPageObj(
            dict["id"], 
            dict["page_number"], 
            dict["content"], 
            dict["content_vector"], 
            dict["keywords"],  
            dict["file_name"], 
            dict["file_path"], 
            dict["detele_flag"], 
            dict["is_contain_image"], 
            dict["image_blob_path"]
        )
    
    def __str__(self):
        return f'id: {self.id}, page_number: {self.page_number}, content: {self.content}, keywords: {self.keywords}, file_name: {self.file_name}, file_path: {self.file_path}, detele_flag: {self.detele_flag}, is_contain_image: {self.is_contain_image}, image_blob_path: {self.image_blob_path}'