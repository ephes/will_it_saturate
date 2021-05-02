# AUTOGENERATED! DO NOT EDIT! File to edit: 03_registry.ipynb (unless otherwise specified).

__all__ = ['register_model', 'get_model_from_registry', 'CLASS_REGISTRY', 'ModelParameters']

# Cell

from pydantic import BaseModel


CLASS_REGISTRY = {}


def register_model(model_class):
    global CLASS_REGISTRY
    CLASS_REGISTRY[model_class.__name__] = model_class
    return model_class


def get_model_from_registry(class_name):
    return CLASS_REGISTRY[class_name]

# Cell


class ModelParameters(BaseModel):
    class_name: str
    parameters: dict

    def to_model(self):
        return get_model_from_registry(self.class_name)(**self.parameters)