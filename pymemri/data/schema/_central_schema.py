# AUTOGENERATED, DO NOT EDIT!
# This file was generated by /tools/generate_central_schema.sh
# Visit https://gitlab.memri.io/memri/schema to learn more

from datetime import datetime
from typing import List, Optional, Union

from pymemri.data.schema.itembase import ItemBase


class Item(ItemBase):
    # Properties
    id: Optional[str] = None
    dateCreated: Optional[datetime] = None
    dateModified: Optional[datetime] = None
    dateServerModified: Optional[datetime] = None
    # TODO: the hell is that
    externalId: Optional[str] = None

    # TODO: label on every item? Seriously?
    # Edges
    language: List["Language"] = []
    label: List["CategoricalPrediction"] = []
    translation: List["Translation"] = []


class Account(Item):
    # Properties
    avatarUrl: Optional[str] = None
    authEmail: Optional[str] = None
    code: Optional[str] = None
    displayName: Optional[str] = None
    externalId: Optional[str] = None
    handle: Optional[str] = None
    identifier: Optional[str] = None
    isMe: Optional[bool] = None
    itemType: Optional[str] = None
    secret: Optional[str] = None
    service: Optional[str] = None
    accessToken: Optional[str] = None
    refreshToken: Optional[str] = None

    # Edges
    changelog: List["AuditItem"] = []
    cryptoTransaction: List["CryptoTransaction"] = []
    location: List["Location"] = []
    network: List["Network"] = []
    ownCurrency: List["CryptoCurrency"] = []
    owner: List["Person"] = []
    trust: List["Account"] = []
    profilePicture: List["Photo"] = []
    following: List["Account"] = []
    follower: List["Account"] = []


class AuditItem(Item):
    # Properties
    actionname: Optional[str] = None
    content: Optional[str] = None
    date: Optional[datetime] = None


class CVUStoredDefinition(Item):
    # Properties
    definition: Optional[str] = None
    domain: Optional[str] = None
    itemType: Optional[str] = None
    name: Optional[str] = None
    queryStr: Optional[str] = None
    renderer: Optional[str] = None
    selector: Optional[str] = None
    definitionType: Optional[str] = None


class CategoricalPrediction(Item):
    # Properties
    source: Optional[str] = None
    value: Optional[str] = None
    probs: Optional[str] = None

    # Edges
    model: List["Model"] = []


class CreativeWork(Item):
    # Properties
    abstract: Optional[str] = None
    content: Optional[str] = None
    datePublished: Optional[datetime] = None
    itemType: Optional[str] = None
    keyword: Optional[str] = None
    textContent: Optional[str] = None
    title: Optional[str] = None
    transcript: Optional[str] = None

    # Edges
    contentLocation: List["Location"] = []
    file: List["File"] = []
    locationCreated: List["Location"] = []
    writtenBy: List["Person"] = []


class CryptoCurrency(Item):
    # Properties
    myToken: Optional[float] = None
    name: Optional[str] = None
    topic: Optional[str] = None

    # Edges
    currencySetting: List["CurrencySetting"] = []
    picture: List["Photo"] = []


class CryptoKey(Item):
    # Properties
    active: Optional[bool] = None
    itemType: Optional[str] = None
    keystr: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    starred: Optional[bool] = None

    # Edges
    owner: List["Person"] = []


class CryptoTransaction(Item):
    # Properties
    outward: Optional[bool] = None
    quantity: Optional[float] = None

    # Edges
    cryptoCurrency: List["CryptoCurrency"] = []
    relateToOther: List["Account"] = []
    relateToOwner: List["Account"] = []


class CurrencySetting(Item):
    # Properties
    deviceAddress: Optional[str] = None
    profileAddress: Optional[str] = None
    seedPhrase: Optional[str] = None
    tokenAddress: Optional[str] = None

    # Edges
    wallet: List["Wallet"] = []


class Dataset(Item):
    # Properties
    name: Optional[str] = None
    queryStr: Optional[str] = None

    # Edges
    entry: List["DatasetEntry"] = []
    labellingTask: List["LabellingTask"] = []
    datasetType: List["DatasetType"] = []


class DatasetEntry(Item):
    # Properties
    skippedByLabeller: Optional[bool] = None

    # Edges
    data: List[Union["Message", "EmailMessage"]] = []
    annotation: List["CategoricalLabel"] = []


class DatasetType(Item):
    # Properties
    name: Optional[str] = None
    queryStr: Optional[str] = None


class Diet(Item):
    # Properties
    abstract: Optional[str] = None
    content: Optional[str] = None
    datePublished: Optional[datetime] = None
    duration: Optional[int] = None
    itemType: Optional[str] = None
    keyword: Optional[str] = None
    name: Optional[str] = None
    textContent: Optional[str] = None
    title: Optional[str] = None
    transcript: Optional[str] = None

    # Edges
    contentLocation: List["Location"] = []
    file: List["File"] = []
    locationCreated: List["Location"] = []
    writtenBy: List["Person"] = []


# TODO: separate _pod_schema
class File(Item):
    # Properties
    filename: Optional[str] = None
    keystr: Optional[str] = None
    nonce: Optional[str] = None
    sha256: Optional[str] = None
    starred: Optional[bool] = None
    externalId: Optional[str] = None


class Integrator(Item):
    # Properties
    name: Optional[str] = None
    repository: Optional[str] = None


class Label(Item):
    # Properties
    color: Optional[str] = None
    name: Optional[str] = None


class LabelAnnotation(Item):
    # Properties
    allowSharing: Optional[bool] = None
    isSubmitted: Optional[bool] = None


class LabelOption(Item):
    # Properties
    color: Optional[str] = None
    name: Optional[str] = None


class LabellingDataType(Item):
    # Properties
    name: Optional[str] = None
    labelType: Optional[str] = None


class LabellingTask(Item):
    # Properties
    name: Optional[str] = None
    currentLabelOption: Optional[str] = None

    # Edges
    taskType: List["TextClassification"] = []
    labelOption: List["LabelOption"] = []
    view: List["CVUStoredDefinition"] = []


class Language(Item):
    # Properties
    languageCode: Optional[str] = None
    languageName: Optional[str] = None


class Location(Item):
    # Properties
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MediaObject(Item):
    # Properties
    bitrate: Optional[int] = None
    duration: Optional[int] = None
    endTime: Optional[datetime] = None
    fileLocation: Optional[str] = None
    startTime: Optional[datetime] = None

    # Edges
    file: List["File"] = []
    includes: List["Person"] = []


class MedicalCondition(Item):
    # Properties
    conditiontype: Optional[str] = None
    itemType: Optional[str] = None
    name: Optional[str] = None


class MessageChannel(Item):
    # Properties
    encrypted: Optional[bool] = None
    externalId: Optional[str] = None
    name: Optional[str] = None
    topic: Optional[str] = None
    service: Optional[str] = None
    isMock: Optional[bool] = None
    sourceProject: Optional[str] = None

    # Edges
    photo: List["Photo"] = []
    receiver: List["Account"] = []


class Model(Item):
    # Properties
    name: Optional[str] = None
    version: Optional[str] = None


class NavigationItem(Item):
    # Properties
    icon: Optional[str] = None
    itemType: Optional[str] = None
    sequence: Optional[int] = None
    sessionName: Optional[str] = None
    title: Optional[str] = None


class Network(Item):
    # Properties
    name: Optional[str] = None

    # Edges
    website: List["Website"] = []


# TODO: to be removed
class OauthFlow(Item):
    # Properties
    accessToken: Optional[str] = None
    accessTokenSecret: Optional[str] = None
    refreshToken: Optional[str] = None
    service: Optional[str] = None


class Person(Item):
    # Properties
    addressBookId: Optional[str] = None
    birthDate: Optional[datetime] = None
    deathDate: Optional[datetime] = None
    displayName: Optional[str] = None
    email: Optional[str] = None
    firstName: Optional[str] = None
    gender: Optional[str] = None
    lastName: Optional[str] = None
    role: Optional[str] = None
    sexualOrientation: Optional[str] = None
    starred: Optional[bool] = None

    # Edges
    account: List["Account"] = []
    address: List["Address"] = []
    birthPlace: List["Location"] = []
    cryptoKey: List["CryptoKey"] = []
    deathPlace: List["Location"] = []
    diet: List["Diet"] = []
    hasPhoneNumber: List["PhoneNumber"] = []
    label: List["Label"] = []
    me: List["Person"] = []
    medicalCondition: List["MedicalCondition"] = []
    mergedFrom: List["Person"] = []
    profilePicture: List["Photo"] = []
    relationship: List["Relationship"] = []
    website: List["Website"] = []


class PhoneNumber(Item):
    # Properties
    phoneNumber: Optional[str] = None


class Photo(Item):
    # Properties
    name: Optional[str] = None
    caption: Optional[str] = None
    exifData: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    channels: Optional[int] = None
    encoding: Optional[str] = None
    mode: Optional[str] = None
    ocrText: Optional[str] = None

    # Edges
    changelog: List["AuditItem"] = []
    thumbnail: List["File"] = []
    file: List["File"] = []


# TODO: separate _pod_schema
class Plugin(Item):
    # Properties
    bundleImage: Optional[str] = None
    containerImage: Optional[str] = None
    configJson: Optional[str] = None
    config: Optional[str] = None
    dataType: Optional[str] = None
    icon: Optional[str] = None
    pluginDescription: Optional[str] = None
    name: Optional[str] = None
    pluginModule: Optional[str] = None
    pluginName: Optional[str] = None
    pluginType: Optional[str] = None
    gitProjectId: Optional[int] = None

    # Edges
    view: List["CVUStoredDefinition"] = []
    templateSettings: List["TemplateSettings"] = []
    project: List["Project"] = []
    run: List["PluginRun"] = []


# TODO: separate _pod_schema
class PluginRun(Item):
    # Properties
    authUrl: Optional[str] = None
    containerImage: Optional[str] = None
    config: Optional[str] = None
    pluginModule: Optional[str] = None
    pluginName: Optional[str] = None
    progress: Optional[float] = None
    status: Optional[str] = None
    targetItemId: Optional[str] = None
    error: Optional[str] = None
    containerId: Optional[str] = None
    webserverPort: Optional[int] = None

    # Edges
    plugin: List["Plugin"] = []
    view: List["CVUStoredDefinition"] = []
    account: List["Account"] = []
    trigger: List["Trigger"] = []


class Post(Item):
    # Properties
    externalId: Optional[str] = None
    message: Optional[str] = None
    postDate: Optional[datetime] = None
    postType: Optional[str] = None
    isMock: Optional[bool] = None
    sourceProject: Optional[str] = None

    # Edges
    author: List["Account"] = []
    comment: List["Post"] = []
    parent: List["Post"] = []
    photo: List["Photo"] = []


class Project(Item):
    # Properties
    name: Optional[str] = None
    gitlabUrl: Optional[str] = None
    dataSource: Optional[str] = None

    # Edges
    dataset: List["Dataset"] = []


class RSSEntry(Item):
    # Properties
    title: Optional[str] = None
    link: Optional[str] = None
    thumbnail: Optional[str] = None
    published: Optional[datetime] = None
    updated: Optional[datetime] = None
    summary: Optional[str] = None
    summarySource: Optional[str] = None
    fullText: Optional[str] = None
    author: Optional[str] = None
    coarseLabel: Optional[str] = None
    fineLabel: Optional[str] = None
    relevance: Optional[float] = None
    rssFeedId: Optional[str] = None
    isIndexed: Optional[bool] = None


class RSSFeed(Item):
    # Properties
    link: Optional[str] = None
    href: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    published: Optional[datetime] = None
    updated: Optional[datetime] = None
    importIsActive: Optional[bool] = None
    thumbnail: Optional[str] = None

    # Edges
    entry: List["RSSEntry"] = []
    photo: List["RSSEntry"] = []


class RSSFeedSummary(Item):
    # Properties
    category: Optional[str] = None
    content: Optional[str] = None


class Relationship(Item):
    # Properties
    label: Optional[str] = None
    proximityValue: Optional[int] = None

    # Edges
    relationship: List["Person"] = []


class SuggestedMerge(Item):
    # Properties
    score: Optional[float] = None
    task: Optional[str] = None

    # Edges
    mergeFrom: List["Person"] = []


class TemplateSettings(Item):
    # Properties
    templateName: Optional[str] = None
    templateId: Optional[int] = None
    dataSource: Optional[str] = None

    # Edges
    labelOption: List["LabelOption"] = []


class Translation(Item):
    # Properties
    value: Optional[str] = None
    translatedProperty: Optional[str] = None
    srcLang: Optional[str] = None
    tgtLang: Optional[str] = None


# TODO: separate _pod_schema
class Trigger(Item):
    # Properties
    action: Optional[str] = None
    filterCreatedAfter: Optional[datetime] = None
    filterCreatedAfterPropertyName: Optional[str] = None
    pluginRunId: Optional[str] = None
    triggerOn: Optional[str] = None

    # Edges
    trigger: List["PluginRun"] = []


class VoteAction(Item):
    # Properties
    dateExecuted: Optional[datetime] = None


class Wallet(Item):
    # Properties
    name: Optional[str] = None

    # Edges
    picture: List["Photo"] = []


class Website(Item):
    # Properties
    itemType: Optional[str] = None
    url: Optional[str] = None


class WrittenWork(CreativeWork):
    pass


class Indexer(Integrator):
    # Properties
    bundleImage: Optional[str] = None
    icon: Optional[str] = None
    indexerClass: Optional[str] = None
    itemDescription: Optional[str] = None
    queryStr: Optional[str] = None
    runDestination: Optional[str] = None

    # Edges
    indexerRun: List["IndexerRun"] = []


class IndexerRun(Integrator):
    # Properties
    errorMessage: Optional[str] = None
    progress: Optional[float] = None
    progressMessage: Optional[str] = None
    queryStr: Optional[str] = None
    runStatus: Optional[str] = None
    targetDataType: Optional[str] = None

    # Edges
    indexer: List["Indexer"] = []


class CategoricalLabel(LabelAnnotation):
    # Properties
    labelValue: Optional[str] = None


class TextClassification(LabellingDataType):
    pass


class Address(Location):
    # Properties
    city: Optional[str] = None
    itemType: Optional[str] = None
    locationAutoLookupHash: Optional[str] = None
    postalCode: Optional[str] = None
    state: Optional[str] = None
    street: Optional[str] = None

    # Edges
    changelog: List["AuditItem"] = []
    country: List["Country"] = []
    location: List["Location"] = []


class Country(Location):
    # Properties
    name: Optional[str] = None

    # Edges
    flag: List["Photo"] = []
    location: List["Location"] = []


class Message(WrittenWork):
    # Properties
    dateReceived: Optional[datetime] = None
    dateSent: Optional[datetime] = None
    externalId: Optional[str] = None
    service: Optional[str] = None
    subject: Optional[str] = None
    sourceProject: Optional[str] = None
    isMock: Optional[bool] = None

    # Edges
    message: List["Message"] = []
    messageChannel: List["MessageChannel"] = []
    photo: List["Photo"] = []
    receiver: List["Account"] = []
    sender: List["Account"] = []
    label: List["CategoricalPrediction"] = []


class Note(WrittenWork):
    # Properties
    starred: Optional[bool] = None

    # Edges
    label: List["Label"] = []


class EmailMessage(Message):
    # Properties
    starred: Optional[bool] = None

    # Edges
    bcc: List["Account"] = []
    cc: List["Account"] = []
    message: List["EmailMessage"] = []
    replyTo: List["Account"] = []
