using UnityEngine;

/// <summary>
/// 游戏主入口，管理全局 Tick 循环和速度控制
/// </summary>
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [Header("Time Settings")]
    public int currentDay = 1;
    public int currentMonth = 1;
    public int currentYear = 1444;
    public int speed = 3;
    public bool isPaused = true;

    [Header("Tick Timing")]
    public float tickInterval = 0.5f;
    private float tickTimer;

    public event System.Action<int, int, int> OnDayAdvanced;
    public event System.Action OnMonthAdvanced;
    public event System.Action OnYearAdvanced;

    private static readonly int[] DaysInMonth = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Update()
    {
        if (isPaused || speed == 0) return;

        tickTimer += Time.deltaTime;
        float interval = tickInterval / speed;

        while (tickTimer >= interval)
        {
            tickTimer -= interval;
            AdvanceDay();
        }
    }

    void AdvanceDay()
    {
        currentDay++;
        int maxDays = DaysInMonth[currentMonth - 1];

        if (currentDay > maxDays)
        {
            currentDay = 1;
            currentMonth++;
            if (currentMonth > 12)
            {
                currentMonth = 1;
                currentYear++;
                OnYearAdvanced?.Invoke();
            }
            OnMonthAdvanced?.Invoke();
        }

        OnDayAdvanced?.Invoke(currentYear, currentMonth, currentDay);
    }
