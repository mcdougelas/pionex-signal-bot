export default {
  // Ini fungsi yang akan jalan otomatis tiap 15 menit dengan cron */15**** bisa lewat Cloudflare Cron Worker
  async scheduled(event, env, ctx) {
    const now = new Date();
    const jamUTC = now.toISOString();
    const jamLokal = now.toLocaleString("id-ID", { timeZone: "Asia/Jakarta" }); // optional

    // Kirim webhook ke Pipedream
    const res = await fetch("https://menjadi_triger_di.m.pipedream.net", { // ganti dengan webhook trigger di pipedream
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        msg: "Halo dari Cloudflare Cron Worker ⏰",
        utc_time: jamUTC,
        local_time: jamLokal, // optional
      }),
    });

    console.log("Webhook terkirim ✅", jamUTC);
  },
};
