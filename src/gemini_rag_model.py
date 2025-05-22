from google import genai
import pathlib
import os
import io

class RAGChatbot:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.corpus = self.__load_corpus()

    def __load_corpus(self):
        """
            Load documents in corpus folder
        :return:
        """
        corpus_dir_path = os.path.abspath("corpus")
        document_file_paths = []
        document_contents = []
        document_samples = []
        # Get document file paths in corpus folder
        for item in os.listdir(corpus_dir_path):
            document_file_path = os.path.join(corpus_dir_path, item)
            if os.path.isfile(document_file_path):
                document_file_paths.append(pathlib.Path(document_file_path))

        # Read documents
        for doc_file_path in document_file_paths:
            document_contents.append(io.BytesIO(doc_file_path.read_bytes()))

        # Upload document to cached cloud of Gemini
        for doc_content in document_contents:
            document_samples.append(self.client.files.upload(
                file = doc_content,
                config = dict(mime_type="application/pdf")
            ))

        # Return all documents in corpus
        return document_samples

    def generate_content(self, prompt):
        """

        :param prompt:
        :return:
        """
        response = self.client.models.generate_content(
            model = self.model,
            contents = [
                *self.corpus,
                prompt
            ]
        )
        return response.text