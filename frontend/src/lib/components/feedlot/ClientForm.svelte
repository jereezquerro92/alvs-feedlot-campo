<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Create a feedlot client. Writes only through the declared endpoint
  `POST /api/clients/` (a catalog ModelViewSet — clients are master data, editable,
  [[adr-24-feedlot-domain]] rule 3). A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never
  throws (rule 1). `onsaved` receives the created client so the caller decides any
  navigation — the form itself has no side effect ([[adr-22-showcase-ready-components]]
  rule 2). Session + CSRF per [[AUTH]].
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    publicBackendUrl?: string;
    /** Safe no-op default (adr-22 rule 2): a bare mount wires no navigation. */
    onsaved?: ((client: Record<string, any>) => void) | undefined;
  } = $props();

  const kinds = [
    { value: "boarding", label: "Hotelería" },
    { value: "own", label: "Hacienda propia" },
  ];

  let name = $state("");
  let kind = $state("boarding");
  let taxId = $state("");
  let contact = $state("");
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const valid = $derived(name.trim() !== "");

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = { name: name.trim(), kind };
    if (taxId !== "") body.tax_id = taxId.trim();
    if (contact !== "") body.contact = contact.trim();
    try {
      const res = await fetch(`${publicBackendUrl}/api/clients/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": readCsrfTokenFromCookie(),
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        error = await readError(res);
        return;
      }
      const created = await res.json();
      ok = true;
      name = "";
      taxId = "";
      contact = "";
      onsaved?.(created);
    } catch {
      error = t("feedlot_form_error");
    } finally {
      saving = false;
    }
  }

  async function readError(res: Response): Promise<string> {
    try {
      const data = await res.json();
      return typeof data === "string" ? data : JSON.stringify(data);
    } catch {
      return `${t("feedlot_form_error")} (${res.status})`;
    }
  }
</script>

<form class="flex flex-col gap-3" onsubmit={submit}>
  <div class="flex flex-col gap-1.5">
    <Label for="c-name">{t("feedlot_form_client_name")}</Label>
    <Input id="c-name" type="text" bind:value={name} disabled={saving} />
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="c-kind">{t("feedlot_form_client_kind")}</Label>
      <select id="c-kind" class={inputClass} bind:value={kind} disabled={saving}>
        {#each kinds as k (k.value)}
          <option value={k.value}>{k.label}</option>
        {/each}
      </select>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="c-tax">{t("feedlot_form_client_tax_id")}</Label>
      <Input id="c-tax" type="text" bind:value={taxId} disabled={saving} />
    </div>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="c-contact">{t("feedlot_form_client_contact")}</Label>
    <Input id="c-contact" type="text" bind:value={contact} disabled={saving} />
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_client")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
