import time
from fastapi import FastAPI, Body
from models.storage import insert_new_key
app = FastAPI()

@app.post("/key")
async def handle_key(data: dict = Body(...)):
  """
  Handles POST requests to the /key route.

  Args:
      data: A dictionary containing the request body.

  Returns:
      A JSON response with a message or error depending on the validation.
  """

  # Extract the input values
  try:
      apikey = data["apikey"]
      secretkey = data["secretkey"]
      ts = int(time.time()*1000)
      insert_new_key(apikey,secretkey,ts)
  except KeyError:
      return {"message": "Missing required fields in request body."}, 400

  # Perform any additional validation or processing as needed
  # (replace with your specific logic)
  if not all([apikey, secretkey]):
      return {"message": "All fields are required."}, 400

  # Success response (replace with your actual logic)
  return {"message": "Data received successfully!"}
