import { NextResponse } from "next/server"

export async function GET() {
  try {
    // Mock results pentru demonstrație
    const results = {
      total_ads: 2847,
      categories: [
        { category: "technology", count: 654, percentage: 23 },
        { category: "automotive", count: 512, percentage: 18 },
        { category: "food_beverage", count: 398, percentage: 14 },
        { category: "fashion", count: 341, percentage: 12 },
        { category: "beauty", count: 285, percentage: 10 },
        { category: "finance", count: 227, percentage: 8 },
        { category: "travel", count: 198, percentage: 7 },
        { category: "health", count: 156, percentage: 5 },
        { category: "education", count: 76, percentage: 3 },
      ],
      top_brands: [
        { brand: "Samsung", ads: 89, engagement: 0.045 },
        { brand: "Nike", ads: 76, engagement: 0.052 },
        { brand: "Coca-Cola", ads: 68, engagement: 0.038 },
        { brand: "Apple", ads: 54, engagement: 0.067 },
        { brand: "McDonald's", ads: 47, engagement: 0.041 },
        { brand: "BMW", ads: 43, engagement: 0.049 },
        { brand: "L'Oréal", ads: 39, engagement: 0.055 },
        { brand: "Netflix", ads: 35, engagement: 0.062 },
      ],
      monthly_trends: [
        { month: "Ianuarie", ads: 245, growth: 0 },
        { month: "Februarie", ads: 267, growth: 8.9 },
        { month: "Martie", ads: 289, growth: 8.2 },
        { month: "Aprilie", ads: 312, growth: 7.9 },
        { month: "Mai", ads: 298, growth: -4.5 },
        { month: "Iunie", ads: 334, growth: 12.1 },
        { month: "Iulie", ads: 356, growth: 6.6 },
        { month: "August", ads: 341, growth: -4.2 },
        { month: "Septembrie", ads: 378, growth: 10.8 },
        { month: "Octombrie", ads: 392, growth: 3.7 },
        { month: "Noiembrie", ads: 425, growth: 8.4 },
        { month: "Decembrie", ads: 410, growth: -3.5 },
      ],
      top_channels: [
        { channel: "Samsung Romania", ads: 89, avg_views: 125000 },
        { channel: "Nike", ads: 76, avg_views: 98000 },
        { channel: "Coca-Cola Romania", ads: 68, avg_views: 156000 },
        { channel: "Apple", ads: 54, avg_views: 234000 },
        { channel: "McDonald's Romania", ads: 47, avg_views: 87000 },
        { channel: "BMW Romania", ads: 43, avg_views: 112000 },
        { channel: "L'Oréal Paris", ads: 39, avg_views: 76000 },
        { channel: "Netflix Romania", ads: 35, avg_views: 145000 },
      ],
    }

    return NextResponse.json(results)
  } catch (error) {
    console.error("Error fetching analysis results:", error)
    return NextResponse.json(
      {
        error: "Failed to fetch analysis results",
        message: error.message,
      },
      { status: 500 },
    )
  }
}
