using UnityEngine;
using System.Collections.Generic;

/// Renders the political map by recoloring province pixels with owner country colors
public class ProvinceMapRenderer : MonoBehaviour
{
    public SpriteRenderer spriteRenderer;
    private Texture2D sourceMap;
    private Texture2D politicalMap;
    private Color32[] sourcePixels;

    public void Initialize(string provinceBmpPath)
    {
        var bytes = System.IO.File.ReadAllBytes(provinceBmpPath);
        sourceMap = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        sourceMap.filterMode = FilterMode.Point;
        sourceMap.LoadImage(bytes);
        sourcePixels = sourceMap.GetPixels32();
        RefreshPoliticalMap();
    }

    public void RefreshPoliticalMap()
    {
        int w = sourceMap.width, h = sourceMap.height;
        politicalMap = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
        var pixels = new Color32[sourcePixels.Length];

        for (int i = 0; i < sourcePixels.Length; i++)
        {
            var src = sourcePixels[i];
            src.a = 255;
            if (ProvinceData.ColorLookup.TryGetValue(src, out var prov) &&
                CountryData.All.TryGetValue(prov.OwnerCountryId, out var country))
                pixels[i] = country.Color;
            else
                pixels[i] = src;
        }

        politicalMap.SetPixels32(pixels);
        politicalMap.Apply();

        var rect = new Rect(0, 0, w, h);
        spriteRenderer.sprite = Sprite.Create(politicalMap, rect, Vector2.one * 0.5f, 100f);
    }

    public ProvinceData GetProvinceAtScreenPos(Vector2 screenPos, Camera cam)
    {
        var worldPos = cam.ScreenToWorldPoint(screenPos);
        var localPos = spriteRenderer.transform.InverseTransformPoint(worldPos);
        int x = Mathf.FloorToInt((localPos.x + sourceMap.width / 200f) * 100f);
        int y = Mathf.FloorToInt((localPos.y + sourceMap.height / 200f) * 100f);
        if (x < 0 || x >= sourceMap.width || y < 0 || y >= sourceMap.height) return null;

        var pixel = sourcePixels[y * sourceMap.width + x];
        pixel.a = 255;
        return ProvinceData.ColorLookup.TryGetValue(pixel, out var prov) ? prov : null;
    }
}
