using UnityEngine;
using System.IO;

/// Scene entry point: loads data, creates test countries, initializes map
public class GameBootstrap : MonoBehaviour
{
    public ProvinceMapRenderer mapRenderer;

    private static readonly string DataRoot = Path.Combine(Application.streamingAssetsPath, "map-output");

    void Start()
    {
        string csvPath = Path.Combine(DataRoot, "definition.csv");
        ProvinceData.LoadFromCSV(csvPath);

        var ming = CountryData.Create(1, "Ming", new Color32(200, 50, 50, 255), 1);
        var france = CountryData.Create(2, "France", new Color32(50, 50, 200, 255), 100);
        var england = CountryData.Create(3, "England", new Color32(180, 30, 30, 255), 200);

        int i = 0;
        foreach (var prov in ProvinceData.IdLookup.Values)
        {
            var target = (i % 3) switch { 0 => ming, 1 => france, _ => england };
            target.AssignProvince(prov.Id);
            i++;
        }

        string bmpPath = Path.Combine(DataRoot, "provinces.bmp");
        mapRenderer.Initialize(bmpPath);

        GameManager.Instance.OnMonthAdvanced += EconomySystem.Tick;
    }
}
