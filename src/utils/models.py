# External Packages
import openai
import torch
from tqdm import trange

# Internal Packages
from src.utils.state import processor_config, config_file


class OpenAI:
    def __init__(self, model_name, device=None):
        self.model_name = model_name
        if not processor_config or not processor_config.conversation or not processor_config.conversation.openai_api_key:
            raise Exception(f"Set OpenAI API key under processor-config > conversation > openai-api-key in config file: {config_file}")
        openai.api_key = processor_config.conversation.openai_api_key
        self.embedding_dimensions = None

    def encode(self, entries: list[str], device=None, **kwargs):
        embedding_tensors = []

        for index in trange(0, len(entries)):
            # OpenAI models create better embeddings for entries without newlines
            processed_entry = entries[index].replace('\n', ' ')

            try:
                response = openai.Embedding.create(input=processed_entry, model=self.model_name)
                embedding_tensors += [torch.tensor(response.data[0].embedding, device=device)]
                # Use current models embedding dimension, once available
                # Else default to embedding dimensions of the text-embedding-ada-002 model
                self.embedding_dimensions = len(response.data[0].embedding) if not self.embedding_dimensions else 1536
            except Exception as e:
                print(f"Failed to encode entry {index} of length: {len(entries[index])}\n\n{entries[index][:1000]}...\n\n{e}")
                # Use zero embedding vector for entries with failed embeddings
                # This ensures entry embeddings match the order of the source entries
                # And they have minimal similarity to other entries (as zero vectors are always orthogonal to other vector)
                embedding_tensors += [torch.zeros(self.embedding_dimensions, device=device)]

        return torch.stack(embedding_tensors)