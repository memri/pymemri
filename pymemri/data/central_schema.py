# AUTOGENERATED, DO NOT EDIT!
# This file was generated by /tools/generate_central_schema.sh
# Visit https://gitlab.memri.io/memri/schema to learn more

from datetime import datetime
from typing import Optional

from pymemri.data.itembase import Item


class Account(Item):
    description = """An account or subscription, for instance for some online service, or a bank account or wallet."""
    properties = Item.properties + [
        "avatarUrl",
        "authEmail",
        "code",
        "displayName",
        "externalId",
        "handle",
        "identifier",
        "isMe",
        "itemType",
        "secret",
        "service",
        "accessToken",
        "refreshToken",
    ]
    edges = Item.edges + [
        "changelog",
        "cryptoTransaction",
        "location",
        "network",
        "ownCurrency",
        "owner",
        "trust",
    ]

    def __init__(
        self,
        avatarUrl: str = None,
        authEmail: str = None,
        code: str = None,
        displayName: str = None,
        externalId: str = None,
        handle: str = None,
        identifier: str = None,
        isMe: bool = None,
        itemType: str = None,
        secret: str = None,
        service: str = None,
        accessToken: str = None,
        refreshToken: str = None,
        changelog: list = None,
        cryptoTransaction: list = None,
        location: list = None,
        network: list = None,
        ownCurrency: list = None,
        owner: list = None,
        trust: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.avatarUrl: Optional[str] = avatarUrl
        self.authEmail: Optional[str] = authEmail
        self.code: Optional[str] = code
        self.displayName: Optional[str] = displayName
        self.externalId: Optional[str] = externalId
        self.handle: Optional[str] = handle
        self.identifier: Optional[str] = identifier
        self.isMe: Optional[bool] = isMe
        self.itemType: Optional[str] = itemType
        self.secret: Optional[str] = secret
        self.service: Optional[str] = service
        self.accessToken: Optional[str] = accessToken
        self.refreshToken: Optional[str] = refreshToken

        # Edges
        self.changelog: list = changelog if changelog is not None else []
        self.cryptoTransaction: list = cryptoTransaction if cryptoTransaction is not None else []
        self.location: list = location if location is not None else []
        self.network: list = network if network is not None else []
        self.ownCurrency: list = ownCurrency if ownCurrency is not None else []
        self.owner: list = owner if owner is not None else []
        self.trust: list = trust if trust is not None else []


class AuditItem(Item):
    description = """TBD"""
    properties = Item.properties + ["actionname", "content", "date"]
    edges = Item.edges + []

    def __init__(
        self,
        actionname: str = None,
        content: str = None,
        date: datetime = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.actionname: Optional[str] = actionname
        self.content: Optional[str] = content
        self.date: Optional[datetime] = date


class CVUStoredDefinition(Item):
    description = """TBD"""
    properties = Item.properties + [
        "definition",
        "domain",
        "itemType",
        "name",
        "querystr",
        "selector",
    ]
    edges = Item.edges + []

    def __init__(
        self,
        definition: str = None,
        domain: str = None,
        itemType: str = None,
        name: str = None,
        querystr: str = None,
        selector: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.definition: Optional[str] = definition
        self.domain: Optional[str] = domain
        self.itemType: Optional[str] = itemType
        self.name: Optional[str] = name
        self.querystr: Optional[str] = querystr
        self.selector: Optional[str] = selector


class CreativeWork(Item):
    description = """The most generic kind of creative work, including books, movies, photographs, software programs, etc."""
    properties = Item.properties + [
        "abstract",
        "content",
        "datePublished",
        "itemType",
        "keyword",
        "textContent",
        "title",
        "transcript",
    ]
    edges = Item.edges + ["contentLocation", "file", "locationCreated", "writtenBy"]

    def __init__(
        self,
        abstract: str = None,
        content: str = None,
        datePublished: datetime = None,
        itemType: str = None,
        keyword: str = None,
        textContent: str = None,
        title: str = None,
        transcript: str = None,
        contentLocation: list = None,
        file: list = None,
        locationCreated: list = None,
        writtenBy: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.abstract: Optional[str] = abstract
        self.content: Optional[str] = content
        self.datePublished: Optional[datetime] = datePublished
        self.itemType: Optional[str] = itemType
        self.keyword: Optional[str] = keyword
        self.textContent: Optional[str] = textContent
        self.title: Optional[str] = title
        self.transcript: Optional[str] = transcript

        # Edges
        self.contentLocation: list = contentLocation if contentLocation is not None else []
        self.file: list = file if file is not None else []
        self.locationCreated: list = locationCreated if locationCreated is not None else []
        self.writtenBy: list = writtenBy if writtenBy is not None else []


class CryptoCurrency(Item):
    description = """"""
    properties = Item.properties + ["myToken", "name", "topic"]
    edges = Item.edges + ["currencySetting", "picture"]

    def __init__(
        self,
        myToken: float = None,
        name: str = None,
        topic: str = None,
        currencySetting: list = None,
        picture: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.myToken: Optional[float] = myToken
        self.name: Optional[str] = name
        self.topic: Optional[str] = topic

        # Edges
        self.currencySetting: list = currencySetting if currencySetting is not None else []
        self.picture: list = picture if picture is not None else []


class CryptoKey(Item):
    description = """A key used in an cryptography protocol."""
    properties = Item.properties + [
        "active",
        "itemType",
        "keystr",
        "name",
        "role",
        "starred",
    ]
    edges = Item.edges + ["owner"]

    def __init__(
        self,
        active: bool = None,
        itemType: str = None,
        keystr: str = None,
        name: str = None,
        role: str = None,
        starred: bool = None,
        owner: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.active: Optional[bool] = active
        self.itemType: Optional[str] = itemType
        self.keystr: Optional[str] = keystr
        self.name: Optional[str] = name
        self.role: Optional[str] = role
        self.starred: Optional[bool] = starred

        # Edges
        self.owner: list = owner if owner is not None else []


class CryptoTransaction(Item):
    description = """"""
    properties = Item.properties + ["outward", "quantity"]
    edges = Item.edges + ["cryptoCurrency", "relateToOther", "relateToOwner"]

    def __init__(
        self,
        outward: bool = None,
        quantity: float = None,
        cryptoCurrency: list = None,
        relateToOther: list = None,
        relateToOwner: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.outward: Optional[bool] = outward
        self.quantity: Optional[float] = quantity

        # Edges
        self.cryptoCurrency: list = cryptoCurrency if cryptoCurrency is not None else []
        self.relateToOther: list = relateToOther if relateToOther is not None else []
        self.relateToOwner: list = relateToOwner if relateToOwner is not None else []


class CurrencySetting(Item):
    description = """"""
    properties = Item.properties + [
        "deviceAddress",
        "profileAddress",
        "seedPhrase",
        "tokenAddress",
    ]
    edges = Item.edges + ["wallet"]

    def __init__(
        self,
        deviceAddress: str = None,
        profileAddress: str = None,
        seedPhrase: str = None,
        tokenAddress: str = None,
        wallet: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.deviceAddress: Optional[str] = deviceAddress
        self.profileAddress: Optional[str] = profileAddress
        self.seedPhrase: Optional[str] = seedPhrase
        self.tokenAddress: Optional[str] = tokenAddress

        # Edges
        self.wallet: list = wallet if wallet is not None else []


class Diet(Item):
    description = """A strategy of regulating the intake of food to achieve or maintain a specific health-related goal."""
    properties = Item.properties + [
        "abstract",
        "content",
        "datePublished",
        "duration",
        "itemType",
        "keyword",
        "name",
        "textContent",
        "title",
        "transcript",
    ]
    edges = Item.edges + ["contentLocation", "file", "locationCreated", "writtenBy"]

    def __init__(
        self,
        abstract: str = None,
        content: str = None,
        datePublished: datetime = None,
        duration: int = None,
        itemType: str = None,
        keyword: str = None,
        name: str = None,
        textContent: str = None,
        title: str = None,
        transcript: str = None,
        contentLocation: list = None,
        file: list = None,
        locationCreated: list = None,
        writtenBy: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.abstract: Optional[str] = abstract
        self.content: Optional[str] = content
        self.datePublished: Optional[datetime] = datePublished
        self.duration: Optional[int] = duration
        self.itemType: Optional[str] = itemType
        self.keyword: Optional[str] = keyword
        self.name: Optional[str] = name
        self.textContent: Optional[str] = textContent
        self.title: Optional[str] = title
        self.transcript: Optional[str] = transcript

        # Edges
        self.contentLocation: list = contentLocation if contentLocation is not None else []
        self.file: list = file if file is not None else []
        self.locationCreated: list = locationCreated if locationCreated is not None else []
        self.writtenBy: list = writtenBy if writtenBy is not None else []


class File(Item):
    description = """Any file that can be stored on disk."""
    properties = Item.properties + ["filename", "keystr", "nonce", "sha256"]
    edges = Item.edges + []

    def __init__(
        self,
        filename: str = None,
        keystr: str = None,
        nonce: str = None,
        sha256: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.filename: Optional[str] = filename
        self.keystr: Optional[str] = keystr
        self.nonce: Optional[str] = nonce
        self.sha256: Optional[str] = sha256


class Integrator(Item):
    description = """An integrator operates on your database enhances your personal data by inferring facts over existing data and adding those to the database."""
    properties = Item.properties + ["name", "repository"]
    edges = Item.edges + []

    def __init__(self, name: str = None, repository: str = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.name: Optional[str] = name
        self.repository: Optional[str] = repository


class ItemEdgeSchema(Item):
    description = """"""
    properties = Item.properties + ["edgeName", "sourceType", "targetType"]
    edges = Item.edges + []

    def __init__(
        self,
        edgeName: str = None,
        sourceType: str = None,
        targetType: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.edgeName: Optional[str] = edgeName
        self.sourceType: Optional[str] = sourceType
        self.targetType: Optional[str] = targetType


class ItemPropertySchema(Item):
    description = """"""
    properties = Item.properties + ["itemType", "propertyName", "valueType"]
    edges = Item.edges + []

    def __init__(
        self,
        itemType: str = None,
        propertyName: str = None,
        valueType: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.itemType: Optional[str] = itemType
        self.propertyName: Optional[str] = propertyName
        self.valueType: Optional[str] = valueType


class Label(Item):
    description = """Attached to an Item, to mark it to be something."""
    properties = Item.properties + ["color", "name"]
    edges = Item.edges + []

    def __init__(self, color: str = None, name: str = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.color: Optional[str] = color
        self.name: Optional[str] = name


class LabelAnnotation(Item):
    description = """"""
    properties = Item.properties + ["allowSharing", "labels"]
    edges = Item.edges + ["annotatedItem"]

    def __init__(
        self,
        allowSharing: bool = None,
        labels: str = None,
        annotatedItem: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.allowSharing: Optional[bool] = allowSharing
        self.labels: Optional[str] = labels

        # Edges
        self.annotatedItem: list = annotatedItem if annotatedItem is not None else []


class Location(Item):
    description = """The location of something."""
    properties = Item.properties + ["latitude", "longitude"]
    edges = Item.edges + []

    def __init__(self, latitude: float = None, longitude: float = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.latitude: Optional[float] = latitude
        self.longitude: Optional[float] = longitude


class MediaObject(Item):
    description = """A media object, such as an image, video, or audio object embedded in a web page or a downloadable dataset i.e. DataDownload. Note that a creative work may have many media objects associated with it on the same web page. For example, a page about a single song (MusicRecording) may have a music video (VideoObject), and a high and low bandwidth audio stream (2 AudioObject's)."""
    properties = Item.properties + [
        "bitrate",
        "duration",
        "endTime",
        "fileLocation",
        "startTime",
    ]
    edges = Item.edges + ["file", "includes"]

    def __init__(
        self,
        bitrate: int = None,
        duration: int = None,
        endTime: datetime = None,
        fileLocation: str = None,
        startTime: datetime = None,
        file: list = None,
        includes: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.bitrate: Optional[int] = bitrate
        self.duration: Optional[int] = duration
        self.endTime: Optional[datetime] = endTime
        self.fileLocation: Optional[str] = fileLocation
        self.startTime: Optional[datetime] = startTime

        # Edges
        self.file: list = file if file is not None else []
        self.includes: list = includes if includes is not None else []


class MedicalCondition(Item):
    description = """Any condition of the human body that affects the normal functioning of a person, whether physically or mentally. Includes diseases, injuries, disabilities, disorders, syndromes, etc."""
    properties = Item.properties + ["conditiontype", "itemType", "name"]
    edges = Item.edges + []

    def __init__(
        self,
        conditiontype: str = None,
        itemType: str = None,
        name: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.conditiontype: Optional[str] = conditiontype
        self.itemType: Optional[str] = itemType
        self.name: Optional[str] = name


class MessageChannel(Item):
    description = """A chat is a collection of messages."""
    properties = Item.properties + ["encrypted", "externalId", "name", "topic"]
    edges = Item.edges + ["photo", "receiver"]

    def __init__(
        self,
        encrypted: bool = None,
        externalId: str = None,
        name: str = None,
        topic: str = None,
        photo: list = None,
        receiver: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.encrypted: Optional[bool] = encrypted
        self.externalId: Optional[str] = externalId
        self.name: Optional[str] = name
        self.topic: Optional[str] = topic

        # Edges
        self.photo: list = photo if photo is not None else []
        self.receiver: list = receiver if receiver is not None else []


class NavigationItem(Item):
    description = """TBD"""
    properties = Item.properties + [
        "icon",
        "itemType",
        "sequence",
        "sessionName",
        "title",
    ]
    edges = Item.edges + []

    def __init__(
        self,
        icon: str = None,
        itemType: str = None,
        sequence: int = None,
        sessionName: str = None,
        title: str = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.icon: Optional[str] = icon
        self.itemType: Optional[str] = itemType
        self.sequence: Optional[int] = sequence
        self.sessionName: Optional[str] = sessionName
        self.title: Optional[str] = title


class Network(Item):
    description = """A group or system of interconnected people or things, for instance a social network."""
    properties = Item.properties + ["name"]
    edges = Item.edges + ["website"]

    def __init__(self, name: str = None, website: list = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.name: Optional[str] = name

        # Edges
        self.website: list = website if website is not None else []


class Person(Item):
    description = """A person (alive, dead, undead, or fictional)."""
    properties = Item.properties + [
        "addressBookId",
        "birthDate",
        "deathDate",
        "displayName",
        "email",
        "firstName",
        "gender",
        "lastName",
        "role",
        "sexualOrientation",
        "starred",
    ]
    edges = Item.edges + [
        "account",
        "address",
        "birthPlace",
        "cryptoKey",
        "deathPlace",
        "diet",
        "hasPhoneNumber",
        "label",
        "me",
        "medicalCondition",
        "mergedFrom",
        "profilePicture",
        "relationship",
        "website",
    ]

    def __init__(
        self,
        addressBookId: str = None,
        birthDate: datetime = None,
        deathDate: datetime = None,
        displayName: str = None,
        email: str = None,
        firstName: str = None,
        gender: str = None,
        lastName: str = None,
        role: str = None,
        sexualOrientation: str = None,
        starred: bool = None,
        account: list = None,
        address: list = None,
        birthPlace: list = None,
        cryptoKey: list = None,
        deathPlace: list = None,
        diet: list = None,
        hasPhoneNumber: list = None,
        label: list = None,
        me: list = None,
        medicalCondition: list = None,
        mergedFrom: list = None,
        profilePicture: list = None,
        relationship: list = None,
        website: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.addressBookId: Optional[str] = addressBookId
        self.birthDate: Optional[datetime] = birthDate
        self.deathDate: Optional[datetime] = deathDate
        self.displayName: Optional[str] = displayName
        self.email: Optional[str] = email
        self.firstName: Optional[str] = firstName
        self.gender: Optional[str] = gender
        self.lastName: Optional[str] = lastName
        self.role: Optional[str] = role
        self.sexualOrientation: Optional[str] = sexualOrientation
        self.starred: Optional[bool] = starred

        # Edges
        self.account: list = account if account is not None else []
        self.address: list = address if address is not None else []
        self.birthPlace: list = birthPlace if birthPlace is not None else []
        self.cryptoKey: list = cryptoKey if cryptoKey is not None else []
        self.deathPlace: list = deathPlace if deathPlace is not None else []
        self.diet: list = diet if diet is not None else []
        self.hasPhoneNumber: list = hasPhoneNumber if hasPhoneNumber is not None else []
        self.label: list = label if label is not None else []
        self.me: list = me if me is not None else []
        self.medicalCondition: list = medicalCondition if medicalCondition is not None else []
        self.mergedFrom: list = mergedFrom if mergedFrom is not None else []
        self.profilePicture: list = profilePicture if profilePicture is not None else []
        self.relationship: list = relationship if relationship is not None else []
        self.website: list = website if website is not None else []


class PhoneNumber(Item):
    description = """A telephone number, SIP Address."""
    properties = Item.properties + ["phoneNumber"]
    edges = Item.edges + []

    def __init__(self, phoneNumber: str = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.phoneNumber: Optional[str] = phoneNumber


class Plugin(Item):
    description = """Information about a Plugin"""
    properties = Item.properties + [
        "bundleImage",
        "container",
        "dataType",
        "icon",
        "itemDescription",
        "name",
        "pluginModule",
        "pluginName",
        "pluginType",
    ]
    edges = Item.edges + ["view"]

    def __init__(
        self,
        bundleImage: str = None,
        container: str = None,
        dataType: str = None,
        icon: str = None,
        itemDescription: str = None,
        name: str = None,
        pluginModule: str = None,
        pluginName: str = None,
        pluginType: str = None,
        view: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.bundleImage: Optional[str] = bundleImage
        self.container: Optional[str] = container
        self.dataType: Optional[str] = dataType
        self.icon: Optional[str] = icon
        self.itemDescription: Optional[str] = itemDescription
        self.name: Optional[str] = name
        self.pluginModule: Optional[str] = pluginModule
        self.pluginName: Optional[str] = pluginName
        self.pluginType: Optional[str] = pluginType

        # Edges
        self.view: list = view if view is not None else []


class Post(Item):
    description = """Post from social media"""
    properties = Item.properties + ["externalId", "message", "postDate", "type"]
    edges = Item.edges + ["author", "comment", "parent", "photo"]

    def __init__(
        self,
        externalId: str = None,
        message: str = None,
        postDate: datetime = None,
        type: str = None,
        author: list = None,
        comment: list = None,
        parent: list = None,
        photo: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.externalId: Optional[str] = externalId
        self.message: Optional[str] = message
        self.postDate: Optional[datetime] = postDate
        self.type: Optional[str] = type

        # Edges
        self.author: list = author if author is not None else []
        self.comment: list = comment if comment is not None else []
        self.parent: list = parent if parent is not None else []
        self.photo: list = photo if photo is not None else []


class Receipt(Item):
    description = """A bill that describes money owed for some Transaction."""
    properties = Item.properties + ["category", "store", "totalCost"]
    edges = Item.edges + ["file", "photo"]

    def __init__(
        self,
        category: str = None,
        store: str = None,
        totalCost: float = None,
        file: list = None,
        photo: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.category: Optional[str] = category
        self.store: Optional[str] = store
        self.totalCost: Optional[float] = totalCost

        # Edges
        self.file: list = file if file is not None else []
        self.photo: list = photo if photo is not None else []


class Relationship(Item):
    description = (
        """Relation of people, that indicates type of relationship and its value"""
    )
    properties = Item.properties + ["label", "value"]
    edges = Item.edges + ["relationship"]

    def __init__(
        self, label: str = None, value: int = None, relationship: list = None, **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.label: Optional[str] = label
        self.value: Optional[int] = value

        # Edges
        self.relationship: list = relationship if relationship is not None else []


class Setting(Item):
    description = """A setting, named by a key, specifications in JSON format."""
    properties = Item.properties + ["json", "keystr"]
    edges = Item.edges + []

    def __init__(self, json: str = None, keystr: str = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.json: Optional[str] = json
        self.keystr: Optional[str] = keystr


class SuggestedMerge(Item):
    description = """Describes a suggestion to merge two or more items"""
    properties = Item.properties + ["score", "task"]
    edges = Item.edges + ["mergeFrom"]

    def __init__(
        self, score: float = None, task: str = None, mergeFrom: list = None, **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.score: Optional[float] = score
        self.task: Optional[str] = task

        # Edges
        self.mergeFrom: list = mergeFrom if mergeFrom is not None else []


class VoteAction(Item):
    description = """The act casting a vote."""
    properties = Item.properties + ["dateExecuted"]
    edges = Item.edges + []

    def __init__(self, dateExecuted: datetime = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.dateExecuted: Optional[datetime] = dateExecuted


class Wallet(Item):
    description = """"""
    properties = Item.properties + ["name"]
    edges = Item.edges + ["picture"]

    def __init__(self, name: str = None, picture: list = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.name: Optional[str] = name

        # Edges
        self.picture: list = picture if picture is not None else []


class Website(Item):
    description = """A Website is a set of related web pages and other items typically served from a single web domain and accessible via URLs."""
    properties = Item.properties + ["itemType", "url"]
    edges = Item.edges + []

    def __init__(self, itemType: str = None, url: str = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.itemType: Optional[str] = itemType
        self.url: Optional[str] = url


class WrittenWork(CreativeWork):
    description = """A written work, for instance a book, article or note. Doesn't have to be published."""
    properties = CreativeWork.properties + []
    edges = CreativeWork.edges + []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Indexer(Integrator):
    description = """An indexer enhances your personal data by inferring facts over existing data and adding those to the database."""
    properties = Integrator.properties + [
        "bundleImage",
        "icon",
        "indexerClass",
        "itemDescription",
        "querystr",
        "runDestination",
    ]
    edges = Integrator.edges + ["indexerRun"]

    def __init__(
        self,
        bundleImage: str = None,
        icon: str = None,
        indexerClass: str = None,
        itemDescription: str = None,
        querystr: str = None,
        runDestination: str = None,
        indexerRun: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.bundleImage: Optional[str] = bundleImage
        self.icon: Optional[str] = icon
        self.indexerClass: Optional[str] = indexerClass
        self.itemDescription: Optional[str] = itemDescription
        self.querystr: Optional[str] = querystr
        self.runDestination: Optional[str] = runDestination

        # Edges
        self.indexerRun: list = indexerRun if indexerRun is not None else []


class IndexerRun(Integrator):
    description = """A run of a certain Indexer."""
    properties = Integrator.properties + [
        "errorMessage",
        "progress",
        "progressMessage",
        "querystr",
        "runStatus",
        "targetDataType",
    ]
    edges = Integrator.edges + ["indexer"]

    def __init__(
        self,
        errorMessage: str = None,
        progress: float = None,
        progressMessage: str = None,
        querystr: str = None,
        runStatus: str = None,
        targetDataType: str = None,
        indexer: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.errorMessage: Optional[str] = errorMessage
        self.progress: Optional[float] = progress
        self.progressMessage: Optional[str] = progressMessage
        self.querystr: Optional[str] = querystr
        self.runStatus: Optional[str] = runStatus
        self.targetDataType: Optional[str] = targetDataType

        # Edges
        self.indexer: list = indexer if indexer is not None else []


class Address(Location):
    description = """A postal address."""
    properties = Location.properties + [
        "city",
        "itemType",
        "locationAutoLookupHash",
        "postalCode",
        "state",
        "street",
    ]
    edges = Location.edges + ["changelog", "country", "location"]

    def __init__(
        self,
        city: str = None,
        itemType: str = None,
        locationAutoLookupHash: str = None,
        postalCode: str = None,
        state: str = None,
        street: str = None,
        changelog: list = None,
        country: list = None,
        location: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.city: Optional[str] = city
        self.itemType: Optional[str] = itemType
        self.locationAutoLookupHash: Optional[str] = locationAutoLookupHash
        self.postalCode: Optional[str] = postalCode
        self.state: Optional[str] = state
        self.street: Optional[str] = street

        # Edges
        self.changelog: list = changelog if changelog is not None else []
        self.country: list = country if country is not None else []
        self.location: list = location if location is not None else []


class Country(Location):
    description = """A country."""
    properties = Location.properties + ["name"]
    edges = Location.edges + ["flag", "location"]

    def __init__(
        self, name: str = None, flag: list = None, location: list = None, **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.name: Optional[str] = name

        # Edges
        self.flag: list = flag if flag is not None else []
        self.location: list = location if location is not None else []


class Photo(MediaObject):
    description = """An image file."""
    properties = MediaObject.properties + ["caption", "exifData", "name"]
    edges = MediaObject.edges + ["changelog", "label", "thumbnail"]

    def __init__(
        self,
        caption: str = None,
        exifData: str = None,
        name: str = None,
        changelog: list = None,
        label: list = None,
        thumbnail: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.caption: Optional[str] = caption
        self.exifData: Optional[str] = exifData
        self.name: Optional[str] = name

        # Edges
        self.changelog: list = changelog if changelog is not None else []
        self.label: list = label if label is not None else []
        self.thumbnail: list = thumbnail if thumbnail is not None else []


class Message(WrittenWork):
    description = """A single message."""
    properties = WrittenWork.properties + [
        "dateReceived",
        "dateSent",
        "externalId",
        "service",
        "subject",
    ]
    edges = WrittenWork.edges + [
        "message",
        "messageChannel",
        "photo",
        "receiver",
        "sender",
    ]

    def __init__(
        self,
        dateReceived: datetime = None,
        dateSent: datetime = None,
        externalId: str = None,
        service: str = None,
        subject: str = None,
        message: list = None,
        messageChannel: list = None,
        photo: list = None,
        receiver: list = None,
        sender: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.dateReceived: Optional[datetime] = dateReceived
        self.dateSent: Optional[datetime] = dateSent
        self.externalId: Optional[str] = externalId
        self.service: Optional[str] = service
        self.subject: Optional[str] = subject

        # Edges
        self.message: list = message if message is not None else []
        self.messageChannel: list = messageChannel if messageChannel is not None else []
        self.photo: list = photo if photo is not None else []
        self.receiver: list = receiver if receiver is not None else []
        self.sender: list = sender if sender is not None else []


class Note(WrittenWork):
    description = """A file containing a note."""
    properties = WrittenWork.properties + ["starred"]
    edges = WrittenWork.edges + ["label"]

    def __init__(self, starred: bool = None, label: list = None, **kwargs):
        super().__init__(**kwargs)

        # Properties
        self.starred: Optional[bool] = starred

        # Edges
        self.label: list = label if label is not None else []


class EmailMessage(Message):
    description = """A single email message."""
    properties = Message.properties + ["starred"]
    edges = Message.edges + ["bcc", "cc", "message", "replyTo", "inbox"]

    def __init__(
        self,
        starred: bool = None,
        read: bool = None,
        bcc: list = None,
        cc: list = None,
        message: list = None,
        replyTo: list = None,
        inbox: list = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Properties
        self.starred: Optional[bool] = starred
        self.read: Optional[bool] = read

        # Edges
        self.bcc: list = bcc if bcc is not None else []
        self.cc: list = cc if cc is not None else []
        self.message: list = message if message is not None else []
        self.replyTo: list = replyTo if replyTo is not None else []
        self.inbox: list = inbox if inbox is not None else []
