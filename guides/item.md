# Overview

The pod stores your data in a graph datastructure. This graph consists of Items and Edges. An `Item` can be many different things, like an `Account`, `Person`, or `Message`. The schema of an `Item` type is defined by the developer, and can be added to your Pod database.

The Pod schema is dynamic, and can be expanded during runtime. This means that as a plugin developer, you can define your own schema definitions on your plugin, without merging your changes to the [memri central schema](https://gitlab.memri.io/memri/schema). We do recommend adding commonly used schema definitions to this central repository, for which you can open a merge request.

In pymemri, the schema is implemented with Pydantic models. Pydantic is a library for data validation using standard Python type annotations. You can read more about Pydantic in their [docs](https://pydantic-docs.helpmanual.io/).

# General use

## Schema Definitions

Consider the following schema definition for a `Dog` item:

```python
from datetime import datetime
from typing import List, Optional, Union

from pydantic import PrivateAttr

from pymemri.data.schema import Item, Message, Person, Photo


class Dog(Item):
    _hasBeenFed: bool = PrivateAttr(False)

    # Properties
    name: Optional[str] = None
    age: Optional[int] = None
    bites: Optional[bool] = None
    weight: Optional[float] = None
    dateOfBirth: Optional[datetime] = None

    # Edges
    owner: List[Person] = []
    referencedBy: List[Union[Message, Photo]] = []
```

This Item has 5 properties: name, age, bites, weight, and dateOfBirth. Additionally, the annotated types of these properties are all the types the Pod currently supports: `str`, `int`, `bool`, `float`, and `datetime`. At the moment, the Pod does not support mandatory properties, so all properties are annotated as `Optional` with `None` as default value.

Along with these five properties, Dog also has the base properties defined on the `Item` class. These base properties contain fields like `id: str`, and are not important for general use. Every schema definition needs to inherit from \`Item\`.

Edges are annotated as a lists of `Item`s. The possible target types of an edge have to be annotated explicitly in the schema definition, and can only be a subclass of `Item`. For example in the above schema, the `Dog.owner` edge can only point to `Person` items, and the `Dog.referencedBy` edge can point to both `Message` and `Photo` Items through the use of a Union type.

The `Dog` item has a private attribute `_hasBeenFed`. These attributes have to start with an `_`, and have a `PrivateAttr` as default value. It will be ignored in the `Dog` schema, and not exported when calling methods like `Dog.to_json()`. You can read more about private attributes in the [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/models/#private-model-attributes).

## Creating Items

Pydantic automatically creates an `__init__` method when you create your schema definition. This `__init__` method can initialize an item with any properties and edges defined on the `Item`. Private attributes or attributes that are not defined will throw a validation error.

As example, we initialize a `Dog` item, where `dateOfBirth` is not defined, and a Person named Bob is the owner:

```python
dog_owner = Person(firstName="Bob")
my_dog = Dog(
  name="Alice",
  age=3,
  bites=False,
  weight=8.2,
  owner = [dog_owner]
)
```

## Working with Edges

While edges are represented as a list of `Item`s, the internal representation of an edge is an `Edge` object. To create an `Edge` on an item, we use the `Item.add_edge` method:

```python
dog_item = Dog(name="Alice")
owner = Person(firstName="Bob")
owner_edge = dog_item.add_edge("owner", owner)
```

You can retrieve this edge object in various ways:

- the `dog_item.add_edge` method will return the created edge. See the above example
- `dog_item.get_edges("owner")` retrieves a list `List[Edge[Owner]]` containing all owner edges
- `dog_item.get_all_edges()` retrieves the list of all edges defined on `dog_item`
- Edges are stored internally in a dictionary: `dog_item.__edges__: Dict[str, List[Edge]]` contains all edges sorted by edge name.

## Registering new schema definitions in the Pod

When adding an `Item` to the pod, the schema has to be communicated first:

```python
from pymemri.pod.client import PodClient

client = PodClient()
client.add_to_schema(Dog)
```

## Adding items to the Pod

The standard way of adding items and edges to the pod is through Pod the Bulk API. With this method, you can create multiple items and edges with one call to the Pod. The following example creates the the same items and edges as the above section in the Pod database:

```python
from pymemri.pod.client import PodClient
from  pymemri.data.schema import Person
from pymemri.examples.example_schema import Dog

# Create a Dog, a Person, and an owner edge between the two.
dog_item = Dog(name="Alice")
owner = Person(firstName="Bob")
owner_edge = dog_item.add_edge("owner", owner)

# Initialize a PodClient
client = PodClient()

# Add the required schemas, and create the dog, person, and edge.
client.add_to_schema(Person, Dog)
client.bulk_action(
    create_items=[dog_item, owner],
    create_edges=[owner_edge]
)
```

```
2022-09-28 15:34:42.460 | INFO     | pymemri.pod.client:bulk_action:277 - BULK: Writing 3/3 items/edges
2022-09-28 15:34:42.476 | INFO     | pymemri.pod.client:bulk_action:289 - Completed Bulk action, written 3 items/edges
```

## Retrieving Items from the Pod

By calling the bulk API, the dog and person items we just created are automatically assigned an `id`. With this ID, we can check if we were successful in creating the items. Additionally, we can see on the `dog_from_pod` item if the edge was created.

```python
print("Dog ID:", dog_item.id)
print("owner ID:", owner.id)

dog_from_pod = client.get(dog_item.id)
person_from_pod = client.get(owner.id)
assert dog_from_pod.owner[0] is person_from_pod
```

```
Dog ID: 0de96f2fdaad4dc08e8be832b834330b
owner ID: 9f0ce6d36de9412aa8f671d802181fc4
```