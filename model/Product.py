from typing import List, Optional

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI


class Product(BaseModel):
    """Information about a product."""

    # ^ Doc-string for the entity Product.
    # This doc-string is sent to the LLM as the description of the schema Product,
    # and it can help to improve extraction results.

    # Note that:
    # 1. Each field is an `optional` -- this allows the model to decline to extract it!
    # 2. Each field has a `description` -- this description is used by the LLM.
    # Having a good description can help improve extraction results.
    product_name: Optional[str] = Field(..., description="The name of the food")
    # merchant_area: Optional[str] = Field(..., description="The location merchant")
    merchant_name: Optional[str] = Field(..., description="The name of the merchant")
    category: Optional[List[str]] = Field(..., description="The category of the food")
    # description: Optional[str] = Field(..., description="The description of the food")
    min_price: Optional[int] = Field(..., description="Min price in rupiah")
    max_price: Optional[int] = Field(..., description="Max price in rupiah")


class Data(BaseModel):
    """Extracted data about product"""

    # Creates a model so that we can extract multiple entities.
    product: List[Product]