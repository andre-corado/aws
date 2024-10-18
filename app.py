# Basic API with Fast API

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import aiomysql
import redis.asyncio as redis
from datetime import datetime

# Cargar las variables del archivo .env
load_dotenv()
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
REDIS_URL = os.getenv("REDIS_URL")

app = FastAPI()

# Conexión a Redis usando las variables del .env
redis_client = redis.from_url(REDIS_URL)
if not redis_client:
    print("Error connecting to Redis")



# Función para obtener la conexión a MySQL
async def get_mysql_connection():
    return await aiomysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DB
    )



# Modelo para la entrada
class TemperatureInput(BaseModel):
    value: float

@app.post("/setTemperature")
async def set_temperature(data: TemperatureInput):
    # Obtener el timestamp actual
    timestamp = datetime.utcnow()

    # Guardar en Redis
    redis_key = f"temperature:{timestamp.isoformat()}"
    await redis_client.hset(redis_key, mapping={"value": data.value, "timestamp": timestamp.isoformat()})

    # Guardar en MySQL
    conn = await get_mysql_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO temperature (value, timestamp) VALUES (%s, %s)",
                (data.value, timestamp)
            )
        await conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando en MySQL: {str(e)}")
        print(e)
    finally:
        conn.close()

    return {"status": "Temperature saved successfully", "timestamp": timestamp.isoformat()}


