FROM mcr.microsoft.com/playwright:v1.58.2-jammy

WORKDIR /workspace

COPY package.json /workspace/package.json
RUN npm install

COPY . /workspace

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

CMD ["bash"]
