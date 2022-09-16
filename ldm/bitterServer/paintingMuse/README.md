Updating Dependencies / Setting up new PEW Env:
--------------------
`pew new --python 3.10 -r requirements.txt ldm8`


Starting the Server
---------------------
`cd stable-diffusion\ldm\bitterServer`
`pew workon ldm6`
`python .\manage.py runserver`
open browser to http://127.0.0.1:8000/


DB and Migrations
-------------------
python manage.py makemigrations paintingMuse
python manage.py migrate paintingMuse

Example queries
-------------------

query {
  allPaintings {
   id
   title
   artistId
   inspirationImageUrl
  }
}

query {
  painting(paintingId: 1) {
    id
    title
    artistId
    inspirationImageUrl
  }
}

mutation createMutation {
  createPainting(paintingData: {prompt: "A blues musician playing Nintendo Switch at the crossroads", artistId:"1"}) {
    painting {
      id,
      prompt,
      title,
      createdAt,
      artistId
    }
  }
}