import wbgapi as wb

# Venezuela resource rents — all available years
df = wb.data.DataFrame("NY.GDP.TOTL.RT.ZS", ["VEN"], time=range(2010, 2023))
print(df.T)
