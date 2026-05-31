using UnityEngine;
using System.Collections.Generic;
using System.IO;
using System.Linq;

/// Province definition loaded from definition.csv
[System.Serializable]
public class ProvinceData
{
    public int Id;
    public string Name;
    public Color32 Color;
    public Vector2 CenterPosition;
    public int OwnerCountryId;
    public int Population;
    public float Tax;

    public static Dictionary<Color32, ProvinceData> ColorLookup = new();
    public static Dictionary<int, ProvinceData> IdLookup = new();

    public static void LoadFromCSV(string csvPath)
    {
        ColorLookup.Clear();
        IdLookup.Clear();

        foreach (var line in File.ReadAllLines(csvPath).Skip(1))
        {
            var parts = line.Split(';');
            if (parts.Length < 5) continue;

            var province = new ProvinceData
            {
                Id = int.Parse(parts[0]),
                Color = new Color32(byte.Parse(parts[1]), byte.Parse(parts[2]), byte.Parse(parts[3]), 255),
                Name = parts[4],
                Population = 1000,
                Tax = 1.0f
            };

            ColorLookup[province.Color] = province;
            IdLookup[province.Id] = province;
        }
    }
}
