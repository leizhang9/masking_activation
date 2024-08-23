library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity top_masked_cmp is
  generic (
    n_instances           : integer := 30;
    baud_rate             : integer := 921600;
    clk_f_fast            : integer := 100000000;
    clk_f_slow            : integer := 1000000;
    payload_bits          : integer := 8;
    stop_bits             : integer := 1;
    parity                : boolean := True;
    even_parity           : boolean := True;
    L_g            				: positive := 8; -- fixed point width
    D_g            				: positive := 2; -- number of shares
    fp_fractional_bits_g 	: positive := 3
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

architecture arch of top_masked_cmp is

component masked_cmp_trn is
  generic (
    L_g            				: positive := 8; -- fixed point width
    D_g            				: positive := 2; -- number of shares
    fp_fractional_bits_g 	: positive := 3
  );
  port (
    clk_i          : in  std_ulogic;
    rst_i          : in  std_ulogic;
    a_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
    b_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
    rnd_i          : in  std_ulogic_vector (18 * L_g * (D_g - 1) - 1 downto 0);
    start_i        : in  std_logic;
    done_o				 : out std_ulogic;
    c_o            : out std_ulogic_vector (L_g * D_g - 1 downto 0);
    d_o            : out std_ulogic_vector (L_g * D_g - 1 downto 0);
    trn_o          : out std_ulogic_vector (L_g * D_g - 1 downto 0)
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
signal dut_done_delay : std_logic;
signal dut_start : std_logic;
signal dut_start_delay : std_logic;
signal a_buf     : std_logic_vector(L_g * D_g - 1 downto 0);
signal b_buf     : std_logic_vector(L_g * D_g - 1 downto 0);
signal c_buf     : std_logic_vector(L_g * D_g - 1 downto 0);
signal d_buf     : std_logic_vector(L_g * D_g - 1 downto 0);
signal trn_buf   : std_logic_vector(L_g * D_g - 1 downto 0);
signal rnd_buf   : std_logic_vector(18 * L_g - 1 downto 0);

signal a         : std_logic_vector(L_g * D_g - 1 downto 0);
signal b         : std_logic_vector(L_g * D_g - 1 downto 0);
signal c         : std_logic_vector(L_g * D_g - 1 downto 0);
signal d         : std_logic_vector(L_g * D_g - 1 downto 0);
signal trn       : std_logic_vector(L_g * D_g  - 1 downto 0);
signal rnd       : std_logic_vector(18 * L_g - 1 downto 0);

signal busy : std_logic;

type s_vector is array (0 to n_instances) of std_ulogic_vector(L_g * D_g - 1 downto 0);
signal c_int    : s_vector;
signal d_int    : s_vector;
signal trn_int  : s_vector;
signal done_int : std_logic_vector(n_instances downto 0);

attribute DONT_TOUCH : string;
attribute keep : string;

attribute DONT_TOUCH of masked_cmp_trn : component is "true";

begin

  clk_int <= clk_fast and not busy;
  int_rst <= not rst;
  rx_fsm_rst <= int_rst or cmd_fsm_done;

  parity_error <= parity_error_int;
  frame_error <= frame_error_int;

  trigger <= busy;

  z_out : process(c_int, d_int, trn_int, done_int)
  variable tmp0 : std_logic_vector(L_g * D_g - 1 downto 0);
  variable tmp1 : std_logic_vector(L_g * D_g - 1 downto 0);
  variable tmp2 : std_logic_vector(L_g * D_g - 1 downto 0);
  variable tmp3 : std_logic;
  begin
    tmp0 := c_int(0);
    tmp1 := d_int(0);
    tmp2 := trn_int(0);
    tmp3 := done_int(0);
    z_l : for i in 1 to n_instances loop
      tmp0 := tmp0 and c_int(i);
      tmp1 := tmp1 and d_int(i);
      tmp2 := tmp2 and trn_int(i);
      tmp3 := tmp3 and done_int(i);
    end loop;
    dut_done <= tmp3;
    c <= tmp0;
    d <= tmp1;
    trn <= tmp2;
  end process;

  reg : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      dut_start_delay <= dut_start;
      dut_done_delay <= dut_done;
    end if;
  end process;

  buf : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      if int_rst = '1' then
        a_buf  <= (others => '0');
        b_buf  <= (others => '0');
        c_buf  <= (others => '0');
        d_buf  <= (others => '0');
        trn_buf <= (others => '0');
        rnd_buf <= (others => '0');
      elsif dut_start = '1' then
        a_buf  <= a;
        b_buf  <= b;
        rnd_buf <= rnd;
      elsif dut_done = '1' then
        c_buf  <= c;
        d_buf  <= d;
        trn_buf <= trn;
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

  cmd_fsm0 : entity work.cmp_cmd_fsm(behavioral)
  generic map (
    L_g => L_g,
    D_g => D_g,
    fp_fractional_bits_g => fp_fractional_bits_g
  )
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
    dut_done => dut_done_delay,
    dut_start => dut_start,
    dut_a => a,
    dut_b => b,
    dut_rnd => rnd,
    dut_c => c_buf,
    dut_d => d_buf,
    dut_trn => trn_buf
  );

  gen_dut : for i in 0 to n_instances generate
    dut : masked_cmp_trn
      port map (
        clk_i => clk_slow,
        rst_i => int_rst,
        a_i => a_buf,
        b_i => b_buf,
        rnd_i => rnd_buf,
        start_i => dut_start_delay,
        done_o => done_int(i),
        c_o => c_int(i),
        d_o => d_int(i),
        trn_o => trn_int(i)
      );
  end generate;
end architecture;
