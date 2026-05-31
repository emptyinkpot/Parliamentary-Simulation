using System.Linq;

/// Monthly economy tick: collects province tax into country treasury
public static class EconomySystem
{
    public static void Tick()
    {
        foreach (var country in CountryData.All.Values)
        {
            float income = country.OwnedProvinceIds
                .Where(id => ProvinceData.IdLookup.ContainsKey(id))
                .Sum(id => ProvinceData.IdLookup[id].Tax);

            country.Treasury += income;
        }
    }
}
