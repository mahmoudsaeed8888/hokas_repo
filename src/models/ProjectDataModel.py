from .BaseDatamodel import BaseDataModel
from .enums.Database_Enums import Database_Enums
from .db_schemes import Project


class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[Database_Enums.COLLECTION_DATABASE_NAME.value]

    async def ini_collection(self):
        all_collection = await self.db_client.list_collection_names()
        if Database_Enums.COLLECTION_DATABASE_NAME.value not in all_collection :
            self.collection = self.db_client[Database_Enums.COLLECTION_DATABASE_NAME.value]
            indexes = Project.get_indexes()
            for index in indexes :
                index_options = {k: v for k, v in index.items() if k not in ["key", "name"]} 
                await self.collection.create_index(
                    index["key"],
                    name = index["name"],
                    **index_options  # دي علشان تجيب كل حاجه ف ال create_index
                )
    @classmethod
    async def create_instance(cls , db_client: object):
        instance=cls(db_client=db_client)
        await instance.ini_collection()
        return instance



    async def create_project(self, project: Project):
        result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))
        project.id = result.inserted_id
        return project

    async def get_project_or_create_one(self, project_id: str):

        record = await self.collection.find_one({
            "project_id": project_id
        })

        if record is None:
            # create new project
            project = Project(project_id=project_id)
            project = await self.create_project(project=project)

            return project
        
        return Project(**record)

    async def get_all_projects(self, page: int=1, page_size: int=10):

        # count total number of documents
        total_documents = await self.collection.count_documents({})

        # calculate total number of pages
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1

        cursor = self.collection.find().skip( (page-1) * page_size ).limit(page_size)
        projects = []
        async for document in cursor:
            projects.append(
                Project(**document)
            )

        return projects, total_pages
