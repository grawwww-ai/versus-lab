The user wants a stunning animated infographic for a fictional coffee shop "La Molienda" showing coffee cups sold each month in 2026. I need to create a single HTML file with inline CSS and JavaScript, no external resources.

Key requirements:
1. 16:9 full screen (so 1920x1080 or similar aspect ratio)
2. Bar chart with 12 months in order
3. Bars grow with entrance animation
4. Each bar labeled with month and value
5. Highlight best month (July: 4210)
6. Three KPI figures: yearly TOTAL, monthly AVERAGE, BEST MONTH
7. Title and subtitle in Spanish
8. Warm coffee-themed design with good typography and colors
9. Each bar must be HTML/SVG element with data-value attribute
10. Bar heights proportional to values
11. All texts in Spanish
12. No external resources - everything inline

Let me calculate the KPIs:
- Total: 2140+2380+2915+3060+3475+3890+4210+4035+3380+2890+2520+2869 = 37,764
- Average: 37,764 / 12 = 3,147
- Best month: Julio with 4,210

For the design, I'll use warm coffee colors: browns, creams, ambers, dark coffee tones. Typography: I'll use system fonts but style them beautifully.

Animation approach:
- Bars grow from bottom to top with stagger
- KPI numbers count up
- Title/subtitle fade in
- Best month highlight pulse/glow

I'll use SVG for the chart since it's easier to make responsive and animate heights proportionally. Or I could use HTML divs with CSS custom properties for heights. SVG might be better for precise control.

Let me plan the layout:
- Full viewport 16:9 container
- Title area at top
- Chart in middle
- KPI cards at bottom or side

Actually, for a stunning infographic, I'll do:
- Header with title/subtitle
- Main chart area with bars
- KPI cards below chart
- All in a 16:9 container that scales to viewport

Color palette:
- Dark coffee: #2C1810
- Medium coffee: #4A3728
- Light coffee: #8B6914
- Cream: #F5E6D3
- Amber: #D4A574
- Highlight gold: #E8C56D
- Steam white: #FFF8F0

I'll use CSS custom properties for the data values to drive bar heights.

For the bar chart, I'll create SVG with rect elements for bars, each with data-value attribute. The height will be calculated based on max value (4210) and available chart height.

Animation: Use CSS @keyframes for bar growth, with animation-delay for stagger. For counting numbers, use JavaScript IntersectionObserver or just setTimeout on load.

Let me write the complete HTML file.