FROM oven/bun:1 AS build
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM oven/bun:1 AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=4321
COPY --from=build --chown=bun:bun /app/dist ./dist
COPY --from=build --chown=bun:bun /app/package.json ./package.json
COPY --from=build --chown=bun:bun /app/node_modules ./node_modules
EXPOSE 4321
USER bun
CMD ["bun", "./dist/server/entry.mjs"]
