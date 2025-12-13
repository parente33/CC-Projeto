
## Instalação

git clone https://github.com/coreemu/core.git
cd core

sudo docker build -t emane-python -f dockerfiles/Dockerfile.emane-python .

sudo docker build -t core -f dockerfiles/Dockerfile.ubuntu .

Nota: O ficheiro requirements.txt deve estar presente na pasta CORE.

## Execução do CORE

sudo docker run -itd --name core -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
--privileged --init --entrypoint /opt/core/venv/bin/core-daemon core

xhost +local:root

sudo docker exec -it core core-gui

## Execução dos Módulos

Após abrir o core-gui, aceder à diretoria src deste projeto.

Para executar a nave:

python3.13 -m nave

Para executar o rover:

python3.13 -m rover x

Onde x corresponde ao ID pretendido para o rover.

## Ground Control

Abrir o ficheiro HTML presente na pasta src no navegador de sua eleição.
