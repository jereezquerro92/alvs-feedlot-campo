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
# `astro dev` writes its generated types into /app/.astro. Local dev mounts that
# path as an anonymous volume (see compose.yaml), and Docker seeds a volume's
# ownership from the image directory it shadows — so the directory must exist
# here, owned by `bun`, or the volume lands root-owned and the dev server dies
# with EACCES. Unused by the production image, which serves the prebuilt dist.
RUN mkdir -p /app/.astro && chown bun:bun /app/.astro
EXPOSE 4321
USER bun
CMD ["bun", "./dist/server/entry.mjs"]
