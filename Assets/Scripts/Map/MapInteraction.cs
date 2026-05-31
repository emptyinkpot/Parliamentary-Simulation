using UnityEngine;

/// Handles camera pan (WASD/arrows/mouse drag) and zoom (scroll) for 2D orthographic view
public class MapInteraction : MonoBehaviour
{
    public float panSpeed = 5f;
    public float zoomSpeed = 2f;
    public float minZoom = 2f;
    public float maxZoom = 30f;

    private Camera cam;
    private Vector3 dragOrigin;
    private bool isDragging;

    void Awake() => cam = GetComponent<Camera>();

    void Update()
    {
        HandleKeyboardPan();
        HandleMouseDrag();
        HandleZoom();
    }

    void HandleKeyboardPan()
    {
        float h = Input.GetAxisRaw("Horizontal");
        float v = Input.GetAxisRaw("Vertical");
        transform.position += new Vector3(h, v, 0) * (panSpeed * cam.orthographicSize * Time.deltaTime);
    }

    void HandleMouseDrag()
    {
        if (Input.GetMouseButtonDown(2)) { isDragging = true; dragOrigin = cam.ScreenToWorldPoint(Input.mousePosition); }
        if (Input.GetMouseButtonUp(2)) isDragging = false;

        if (isDragging)
        {
            var diff = dragOrigin - cam.ScreenToWorldPoint(Input.mousePosition);
            transform.position += diff;
        }
    }

    void HandleZoom()
    {
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (scroll == 0f) return;
        cam.orthographicSize = Mathf.Clamp(cam.orthographicSize - scroll * zoomSpeed, minZoom, maxZoom);
    }
}
