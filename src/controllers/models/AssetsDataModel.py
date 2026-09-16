from .BaseDatamodel import BaseDataModel
from .enums.Database_Enums import Database_Enums
from .db_schemes import Assets
from bson import ObjectId

class AssetsModel(BaseDataModel):
    def __init__(self,db_client :object):
        super().__init__(db_client=db_client)
        self.collection= self.db_client[Database_Enums.COLLECTION_ASSETS_NAME.value]

    async def ini_collection(self):
         all_collection = await self.db_client.list_collection_names()
         if Database_Enums.COLLECTION_ASSETS_NAME.value not in all_collection :
             self.collection = self.db_client[Database_Enums.COLLECTION_ASSETS_NAME.value]
             indexes = Assets.get_indexes()
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

    async def create_asset(self, asset: Assets):
        result = await self.collection.insert_one(asset.dict(by_alias=True, exclude_unset=True))
        asset.id = result.inserted_id
        return asset

    async def get_all_project_assets(self, asset_project_id: ObjectId, asset_type :str):
        records = await self.collection.find({
            "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
            "asset_type" : asset_type
        }).to_list(length=None)
        
        return[
            Assets(**record)
            for record in records 
        ]
    
    async def get_one_assets(self,asset_project_id :ObjectId,asset_name :str) :
        result = await self.collection.find_one({
            "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
            "asset_name" : asset_name

        })
        if result :
            return Assets(**result)
        else :
            return None 

