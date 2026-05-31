using UnityEngine;
using System.Collections.Generic;

/// Country definition with owned provinces and treasury
[System.Serializable]
public class CountryData
{
    public int Id;
    public string Name;
    public Color32 Color;
    public int CapitalProvinceId;
    public float Treasury;
    public List<int> OwnedProvinceIds = new();

    public static Dictionary<int, CountryData> All = new();

    public static CountryData Create(int id, string name, Color32 color, int capitalId)
    {
        var country = new CountryData
        {
            Id = id,
            Name = name,
            Color = color,
            CapitalProvinceId = capitalId,
            Treasury = 100f
        };
        All[id] = country;
        return country;
    }

    public void AssignProvince(int provinceId)
    {
        if (!OwnedProvinceIds.Contains(provinceId))
            OwnedProvinceIds.Add(provinceId);

        if (ProvinceData.IdLookup.TryGetValue(provinceId, out var prov))
            prov.OwnerCountryId = Id;
    }
}
