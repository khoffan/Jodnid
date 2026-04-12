/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: "https://jodnid-home.vercel.app", // เปลี่ยนเป็น URL จริงของคุณ
  generateRobotsTxt: true, // สร้าง robots.txt ให้ด้วย
  sitemapSize: 7000,
  robotsTxtOptions: {
    policies: [
      {
        userAgent: "*",
        allow: "/",
      },
    ],
  },
};
