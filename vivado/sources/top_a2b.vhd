library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity top_a2b is
  generic (
    n_instances : integer := 2;
    baud_rate : integer := 921600;
    clk_f_fast : integer := 100000000;
    clk_f_slow : integer := 1000000;
    payload_bits : integer := 8;
    stop_bits : integer := 1;
    parity : boolean := True;
    even_parity : boolean := True
  );
  port (
    clk_fast : in std_logic;
    clk_slow : in std_logic;
    rst : in std_logic;

    parity_error : out std_logic;
    frame_error : out std_logic;
    uart_rx : in std_logic;
    uart_tx : out std_logic;
    led_idle : out std_logic;

    trigger : out std_logic
  );
end entity;

architecture arch of top_a2b is

component convert_a_to_b is
    port (
        clk   : in std_logic;
        rst   : in std_logic;
        start : in std_logic;
        A0    : in std_logic_vector(n_bit - 1 downto 0);
        A1    : in std_logic_vector(n_bit - 1 downto 0);
        r0    : in std_logic_vector(n_bit - 1 downto 0);
        r1    : in std_logic_vector(n_bit - 1 downto 0);
        r2    : in std_logic_vector(n_bit - 2 downto 0);
        r3    : in std_logic_vector(n_bit - 2 downto 0);
        r4    : in std_logic_vector(n_bit - 2 downto 0);
        done  : out std_logic;
        z0    : out std_logic_vector(n_bit - 1 downto 0);
        z1    : out std_logic_vector(n_bit - 1 downto 0)
    );
end component;

signal clk_int : std_logic;
signal int_rst : std_logic;

signal rx_data : std_ulogic_vector(7 downto 0);
signal rx_valid : std_logic;
signal tx_data : std_logic_vector(7 downto 0);
signal tx_valid : std_logic;
signal tx_rdy : std_logic;
signal parity_error_int : std_logic;
signal frame_error_int : std_logic;
signal parity_error_en : std_logic;
signal frame_error_en : std_logic;

signal command : std_logic_vector(7 downto 0);
signal length : std_logic_vector(7 downto 0);
signal payload : std_logic_vector(7 downto 0);
signal new_cmd : std_logic;
signal new_payload : std_logic;

signal rx_fsm_rst : std_logic;
signal cmd_fsm_done : std_logic;

signal dut_done : std_logic;
signal dut_start : std_logic;
signal dut_start_delay : std_logic;
signal A0_buf    : std_logic_vector(n_bit - 1 downto 0);
signal A1_buf    : std_logic_vector(n_bit - 1 downto 0);
signal r0_buf    : std_logic_vector(n_bit - 1 downto 0);
signal r1_buf    : std_logic_vector(n_bit - 1 downto 0);
signal r2_buf    : std_logic_vector(n_bit - 2 downto 0);
signal r3_buf    : std_logic_vector(n_bit - 2 downto 0);
signal r4_buf    : std_logic_vector(n_bit - 2 downto 0);

signal A0    : std_logic_vector(n_bit - 1 downto 0);
signal A1    : std_logic_vector(n_bit - 1 downto 0);
signal r0    : std_logic_vector(n_bit - 1 downto 0);
signal r1    : std_logic_vector(n_bit - 1 downto 0);
signal r2    : std_logic_vector(n_bit - 2 downto 0);
signal r3    : std_logic_vector(n_bit - 2 downto 0);
signal r4    : std_logic_vector(n_bit - 2 downto 0);
signal z0 : std_logic_vector(n_bit - 1 downto 0);
signal z1 : std_logic_vector(n_bit - 1 downto 0);

signal busy : std_logic;

type s_vector is array (0 to n_instances) of std_logic_vector(n_bit - 1 downto 0);
signal z0_int : s_vector;
signal z1_int : s_vector;
signal done_int : std_logic_vector(n_instances downto 0);

attribute DONT_TOUCH : string;
attribute keep : string;

attribute DONT_TOUCH of convert_a_to_b : component is "true";

attribute keep of A0 : signal is "true";
attribute keep of A1 : signal is "true";
attribute keep of r0 : signal is "true";
attribute keep of r1 : signal is "true";
attribute keep of r2 : signal is "true";
attribute keep of r3 : signal is "true";
attribute keep of r4 : signal is "true";

begin

  clk_int <= clk_fast and not busy;
  int_rst <= not rst;
  rx_fsm_rst <= int_rst or cmd_fsm_done;

  parity_error <= parity_error_int;
  frame_error <= frame_error_int;

  trigger <= busy;

  z_out : process(z0_int, z1_int, done_int)
  variable tmp0 : std_logic_vector(n_bit - 1 downto 0);
  variable tmp1 : std_logic_vector(n_bit - 1 downto 0);
  variable tmp2 : std_logic;
  begin
    tmp0 := z0_int(0);
    tmp1 := z1_int(0);
    tmp2 := done_int(0);
    z_l : for i in 1 to n_instances - 1 loop
      tmp0 := tmp0 and z0_int(i);
      tmp1 := tmp1 and z1_int(i);
      tmp2 := tmp2 and done_int(i);
    end loop;
    dut_done <= tmp2;
    z0 <= tmp0;
    z1 <= tmp1;
  end process;

  reg : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      dut_start_delay <= dut_start;
    end if;
  end process;

  buf : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      if int_rst = '1' then
        A0_buf <= (others => '0');
        A1_buf <= (others => '0');
        r0_buf <= (others => '0');
        r1_buf <= (others => '0');
        r2_buf <= (others => '0');
        r3_buf <= (others => '0');
        r4_buf <= (others => '0');
      elsif dut_start = '1' then
        A0_buf <= A0;
        A1_buf <= A1;
        r0_buf <= r0;
        r1_buf <= r1;
        r2_buf <= r2;
        r3_buf <= r3;
        r4_buf <= r4;
      end if;
    end if;
  end process;

  trig_reg : process(clk_fast)
  begin
    if clk_fast'event and clk_fast = '1' then
      if rx_fsm_rst = '1' then
        busy <= '0';
      else
        if dut_done = '1' then
          busy <= '0';
        elsif dut_start = '1' then
          busy <= '1';
        end if;
      end if;
    end if;
  end process;

  led : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      if int_rst = '1' then
        led_idle <= '0';
      else
        led_idle <= not busy;
      end if;
    end if;
  end process;

  p_error : process(clk_int)
  begin
    if clk_int'event and clk_int = '1' then
      if int_rst = '1' then
        parity_error_int <= '0';
      elsif parity_error_en = '1' then
        parity_error_int <= '1';
      end if;
    end if;
  end process;

  f_error : process(clk_int)
  begin
    if clk_int'event and clk_int = '1' then
      if int_rst = '1' then
        frame_error_int <= '0';
      elsif frame_error_en = '1' then
        frame_error_int <= '1';
      end if;
    end if;
  end process;

  uart : entity work.uart_if(behavioral)
  generic map (
    BAUD_RATE_G => baud_rate,
    CLK_FREQ_G => clk_f_fast,
    EN_PARITY_G => parity,
    EVEN_PARITY_G => even_parity,
    N_PAYLOAD_BITS_G => payload_bits,
    N_STOP_BITS_G => stop_bits
  )
  port map (
    axis_aclk => clk_int,
    axis_rst => int_rst,
    parity_error => parity_error_en,
    frame_error => frame_error_en,
    txd => uart_tx,
    rxd => uart_rx,
    s_axis_tdata => std_ulogic_vector(tx_data),
    s_axis_tvalid => tx_valid,
    s_axis_tready => tx_rdy,
    m_axis_tdata => rx_data,
    m_axis_tvalid => rx_valid
  );

  rx_fsm0 : entity work.rx_fsm(behavioral)
  port map (
    clk => clk_int,
    rst => rx_fsm_rst,
    rx_data => std_logic_vector(rx_data),
    rx_valid => rx_valid,
    command => command,
    length => length,
    payload => payload,
    new_cmd => new_cmd,
    new_payload => new_payload
  );

  cmd_fsm0 : entity work.a2b_cmd_fsm(behavioral)
  port map (
    clk => clk_int,
    clk_slow => clk_slow,
    rst => int_rst,
    tx_data => tx_data,
    tx_valid => tx_valid,
    tx_rdy => tx_rdy,
    command => command,
    length => length,
    payload => payload,
    new_cmd => new_cmd,
    new_payload => new_payload,
    done => cmd_fsm_done,
    dut_done => dut_done,
    dut_start => dut_start,
    A0 => A0,
    A1 => A1,
    r0 => r0,
    r1 => r1,
    r2 => r2,
    r3 => r3,
    r4 => r4,
    z0 => z0,
    z1 => z1
  );

  gen_dut : for i in 0 to n_instances - 1 generate
    dut : convert_a_to_b
      port map (
        clk => clk_slow,
        rst => int_rst,
        start => dut_start_delay,
        A0 => A0_buf,
        A1 => A1_buf,
        r0 => r0_buf,
        r1 => r1_buf,
        r2 => r2_buf,
        r3 => r3_buf,
        r4 => r4_buf,
        done => done_int(i),
        z0 => z0_int(i),
        z1 => z1_int(i)
      );
  end generate;
end architecture;
