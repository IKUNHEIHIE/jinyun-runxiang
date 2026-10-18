# ==========================================
# 阶段 1: 依赖安装与静态资源构建
# ==========================================
FROM node:20-alpine AS build-stage

WORKDIR /app

RUN npm config set registry https://registry.npmmirror.com

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

COPY . .
RUN npm run build

# ==========================================
# 阶段 2: Nginx 生产环境静态托管
# ==========================================
FROM nginx:stable-alpine AS production-stage
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
