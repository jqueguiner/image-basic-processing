# Docker for API

You can build and run the docker using the following process:

Cloning
```console
git clone https://github.com/jqueguiner/image-basic-processing image-basic-processing
```

Building Docker
```console
cd image-basic-processing && docker build -t image-basic-processing -f Dockerfile .
```

Running Docker
```console
echo "http://$(curl ifconfig.io):5000" && docker run -p 5000:5000 -d image-basic-processing
```

Calling the API
```console
curl -X POST "http://MY_SUPER_API_IP:5000/rotate" -H "accept: image/*" -H "Content-Type: application/json" -d '{"url":"https://i.ibb.co/BGHyHjc/input.png", "angle": "30"}' --output rotate_image.png
curl -X POST "http://MY_SUPER_API_IP:5000/flip" -H "accept: image/*" -H "Content-Type: application/json" -d '{"url":"https://i.ibb.co/BGHyHjc/input.png", "mode": "vertical"}' --output flip_image.png
```
