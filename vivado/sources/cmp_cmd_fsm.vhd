library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.conversion_pkg.all;

entity cmp_cmd_fsm is
  generic (
		L_g            				: positive := 8; -- fixed point width
		D_g            				: positive := 2; -- number of shares
		fp_fractional_bits_g 	: positive := 3
	);
  port (
    clk               : in std_logic;
    clk_slow          : in std_logic;
    rst               : in std_logic;

    -- uart
    tx_data           : out std_logic_vector(7 downto 0);
    tx_valid          : out std_ulogic;
    tx_rdy            : in std_logic;

    -- command signals
    command           : in std_logic_vector(7 downto 0);
    length            : in std_logic_vector(7 downto 0);
    payload           : in std_logic_vector(7 downto 0);
    new_cmd           : in std_logic;
    new_payload       : in std_logic;
    done              : out std_logic;

    -- dut signals
		dut_a             : out  std_ulogic_vector (L_g * D_g - 1 downto 0);
		dut_b             : out  std_ulogic_vector (L_g * D_g - 1 downto 0);
		dut_rnd           : out  std_ulogic_vector (18 * L_g * (D_g - 1) - 1 downto 0);
    dut_start         : out  std_logic;
		dut_done				  : in   std_logic;
		dut_c             : in   std_logic_vector (L_g * D_g - 1 downto 0);
		dut_d             : in   std_logic_vector (L_g * D_g - 1 downto 0);
		dut_trn           : in   std_logic_vector (L_g * D_g - 1 downto 0)
  );
end entity;

architecture behavioral of cmp_cmd_fsm is

  -- fsm signals
  type states is (RESET, IDLE, WR_A0, WAIT_A0, WR_A1, WAIT_A1, WR_B0, WAIT_B0, WR_B1, WAIT_B1, WR_RAND, WAIT_RAND, INC_RAND, PROC_DONE, SEND_ACK, WAIT_SEND_ACK, WAIT_TX, WAIT_DUT, START_DUT, SEND_C0, WAIT_SEND_C0, SEND_C1, WAIT_SEND_C1, SEND_D0, WAIT_SEND_D0, SEND_D1, WAIT_SEND_D1, SEND_TRN0, WAIT_SEND_TRN0, SEND_TRN1, WAIT_SEND_TRN1);
  signal c_state : states;
  signal n_state : states;

  signal rst_int : std_logic;

  -- dut signals
  signal a0_reg   : std_logic_vector(L_g - 1 downto 0);
  signal a1_reg   : std_logic_vector(L_g - 1 downto 0);
  signal a0_en    : std_logic;
  signal a1_en    : std_logic;

  signal b0_reg   : std_logic_vector(L_g - 1 downto 0);
  signal b1_reg   : std_logic_vector(L_g - 1 downto 0);
  signal b0_en    : std_logic;
  signal b1_en    : std_logic;

  signal rnd_reg : std_logic_vector(18 * L_g * (D_g - 1) - 1 downto 0);
  signal rnd_en  : std_logic_vector(18 downto 0);

  signal cnt : unsigned(18 downto 0);
  signal cnt_en : std_logic;
  signal cnt_rst : std_logic;

  signal data_cnt : natural range 0 to 19;
  signal rst_data_cnt : std_logic;

  signal dut_start_int : std_logic;
  signal lock : std_logic;

begin

  dut_start <= dut_start_int;
  dut_a <= std_ulogic_vector(a0_reg & a1_reg);
  dut_b <= std_ulogic_vector(b0_reg & b1_reg);
  dut_rnd <= std_ulogic_vector(rnd_reg);

  lock_reg : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      if rst = '1' or dut_done = '1' then
        lock <= '0';
      elsif dut_start_int = '1' then
        lock <= '1';
      else
        lock <= lock;
      end if;
    end if;
  end process;

  start_reg : process(clk_slow)
  begin
    if clk_slow'event and clk_slow = '1' then
      if rst = '1' or dut_done = '1' then
        dut_start_int <= '0';
      elsif c_state = START_DUT and lock = '0' then
        dut_start_int <= '1';
      else
        dut_start_int <= '0';
      end if;
    end if;
  end process;

  data_counter : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' or new_cmd = '1' or rst_data_cnt = '1' then
        data_cnt <= 0;
      elsif new_payload = '1' then
        data_cnt <= data_cnt + 1;
      end if;
    end if;
  end process;

  rand_enable : process(c_state, cnt)
  begin
    if c_state = WR_RAND then
      rnd_en <= std_logic_vector(cnt);
    else
      rnd_en <= (others => '0');
    end if;
  end process;

  counter : process(clk)
  begin
    if clk'event and clk = '1' then
      if cnt_rst = '1' then
        cnt <= (others => '0');
      elsif cnt_en = '1' then
        if to_integer(cnt) = 0 then
          cnt(0) <= '1';
        else
          cnt <= shift_left(cnt, 1);
        end if;
      end if;
    end if;
  end process;

  reg : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        a0_reg    <= (others => '0');
        a1_reg    <= (others => '0');
        b0_reg    <= (others => '0');
        b1_reg    <= (others => '0');
        rnd_reg   <= (others => '0');
      else
        if a0_en = '1' then
          a0_reg <= payload;
        end if;
        if a1_en = '1' then
          a1_reg <= payload;
        end if;
        if b0_en = '1' then
          b0_reg <= payload;
        end if;
        if b1_en = '1' then
          b1_reg <= payload;
        end if;

        en_loop : for i in 0 to 17 loop
          if rnd_en(i) = '1' then
            rnd_reg((i + 1) * L_g - 1 downto i * L_g) <= payload;
          end if;
        end loop;

      end if;
    end if;
  end process;

  n_logic : process(c_state, rst, new_cmd, command, new_payload, length, data_cnt, dut_done, tx_rdy, cnt, lock)
  begin
    case(c_state) is
      when RESET =>
        if rst = '1' then
          n_state <= RESET;
        else
          n_state <= IDLE;
        end if;

      when IDLE =>
        if new_cmd = '1' then
          if command = x"01" then
            n_state <= WAIT_A0;
          elsif command = x"02" then
            n_state <= WAIT_RAND;
          elsif command = x"03" then
            n_state <= START_DUT;
          else
            n_state <= RESET;
          end if;
        elsif data_cnt >= to_integer(unsigned(length)) and data_cnt > 0 then
          n_state <= WAIT_SEND_ACK;
        else
          n_state <= IDLE;
        end if;

      when WAIT_A0 =>
        if new_payload = '1' then
          n_state <= WR_A0;
        else
          n_state <= WAIT_A0;
        end if;

      when WR_A0 =>
        n_state <= WAIT_A1;

      when WAIT_A1 =>
        if new_payload = '1' then
          n_state <= WR_A1;
        else
          n_state <= WAIT_A1;
        end if;

      when WR_A1 =>
        n_state <= WAIT_B0;

      when WAIT_B0 =>
        if new_payload = '1' then
          n_state <= WR_B0;
        else
          n_state <= WAIT_B0;
        end if;

      when WR_B0 =>
        n_state <= WAIT_B1;

      when WAIT_B1 =>
        if new_payload = '1' then
          n_state <= WR_B1;
        else
          n_state <= WAIT_B1;
        end if;

      when WR_B1 =>
        n_state <= IDLE;

      when WR_RAND =>
        if cnt(17) = '1' then
          n_state <= IDLE;
        else
          n_state <= WAIT_RAND;
        end if;

      when WAIT_RAND =>
        if new_payload = '1' then
          n_state <= INC_RAND;
        else
          n_state <= WAIT_RAND;
        end if;

      when INC_RAND =>
        n_state <= WR_RAND;

      when PROC_DONE =>
        n_state <= IDLE;

      when WAIT_SEND_ACK =>
        if tx_rdy = '1' then
          n_state <= SEND_ACK;
        else
          n_state <= WAIT_SEND_ACK;
        end if;

      when SEND_ACK =>
        n_state <= WAIT_TX;

      when WAIT_TX =>
        if tx_rdy = '1' then
          n_state <= PROC_DONE;
        else
          n_state <= WAIT_TX;
        end if;

      when START_DUT =>
        if lock = '1' then
          n_state <= WAIT_DUT;
        else
          n_state <= START_DUT;
        end if;

      when WAIT_DUT =>
        if dut_done = '1' then
          n_state <= SEND_C0;
        else
          n_state <= WAIT_DUT;
        end if;

      when SEND_C0 =>
        n_state <= WAIT_SEND_C0;

      when WAIT_SEND_C0 =>
        if tx_rdy = '1' then
          n_state <= SEND_C1;
        else
          n_state <= WAIT_SEND_C0;
        end if;

      when SEND_C1 =>
        n_state <= WAIT_SEND_C1;

      when WAIT_SEND_C1 =>
        if tx_rdy = '1' then
          n_state <= SEND_D0;
        else
          n_state <= WAIT_SEND_C1;
        end if;

      when SEND_D0 =>
        n_state <= WAIT_SEND_D0;

      when WAIT_SEND_D0 =>
        if tx_rdy = '1' then
          n_state <= SEND_D1;
        else
          n_state <= WAIT_SEND_D0;
        end if;

      when SEND_D1 =>
        n_state <= WAIT_SEND_D1;

      when WAIT_SEND_D1 =>
        if tx_rdy = '1' then
          n_state <= SEND_TRN0;
        else
          n_state <= WAIT_SEND_D1;
        end if;

      when SEND_TRN0 =>
        n_state <= WAIT_SEND_TRN0;

      when WAIT_SEND_TRN0 =>
        if tx_rdy = '1' then
          n_state <= SEND_TRN1;
        else
          n_state <= WAIT_SEND_TRN0;
        end if;

      when SEND_TRN1 =>
        n_state <= WAIT_SEND_TRN1;

      when WAIT_SEND_TRN1 =>
        if tx_rdy = '1' then
          n_state <= PROC_DONE;
        else
          n_state <= WAIT_SEND_TRN1;
        end if;

      when others =>
        n_state <= RESET;
    end case;
  end process;


  o_logic : process(c_state)
  begin
    a0_en <= '0';
    a1_en <= '0';
    b0_en <= '0';
    b1_en <= '0';
    rst_int <= '0';
    cnt_rst <= '0';
    cnt_en <= '0';
    done <= '0';
    rst_data_cnt <= '0';
    tx_valid <= '0';
    tx_data <= (others => '0');
    case(c_state) is
      when WR_A0 =>
        a0_en <= '1';
      when WR_A1 =>
        a1_en <= '1';
      when WR_B0 =>
        b0_en <= '1';
      when WR_B1 =>
        b1_en <= '1';
      when INC_RAND =>
        cnt_en <= '1';
      when RESET =>
        rst_int <= '1';
        cnt_rst <= '1';
      when SEND_ACK =>
        tx_valid <= '1';
        tx_data <= x"01";
        cnt_rst <= '1';
      when WAIT_TX =>
        tx_data <= x"01";
      when PROC_DONE =>
        done <= '1';
        rst_data_cnt <= '1';
      when SEND_C0 =>
        tx_valid <= '1';
        tx_data <= dut_c(L_g * D_g - 1 downto L_g);
      when SEND_C1 =>
        tx_valid <= '1';
        tx_data <= dut_c(L_g - 1 downto 0);
      when WAIT_SEND_C0 =>
        tx_data <= dut_c(L_g * D_g - 1 downto L_g);
      when WAIT_SEND_C1 =>
        tx_data <= dut_c(L_g - 1 downto 0);
      when SEND_D0 =>
        tx_valid <= '1';
        tx_data <= dut_d(L_g * D_g - 1 downto L_g);
      when SEND_D1 =>
        tx_valid <= '1';
        tx_data <= dut_d(L_g - 1 downto 0);
      when WAIT_SEND_D0 =>
        tx_data <= dut_d(L_g * D_g - 1 downto L_g);
      when WAIT_SEND_D1 =>
        tx_data <= dut_d(L_g - 1 downto 0);
      when SEND_TRN0 =>
        tx_valid <= '1';
        tx_data <= dut_trn(L_g * D_g - 1 downto L_g);
      when SEND_TRN1 =>
        tx_valid <= '1';
        tx_data <= dut_trn(L_g - 1 downto 0);
      when WAIT_SEND_TRN0 =>
        tx_data <= dut_trn(L_g * D_g - 1 downto L_g);
      when WAIT_SEND_TRN1 =>
        tx_data <= dut_trn(L_g - 1 downto 0);
      when others =>
        a0_en <= '0';
        a1_en <= '0';
        b0_en <= '0';
        b1_en <= '0';
        rst_int <= '0';
        cnt_rst <= '0';
        cnt_en <= '0';
        done <= '0';
        tx_valid <= '0';
        tx_data <= (others => '0');
    end case;
  end process;

  state_mem : process(clk)
  begin
    if clk'event and clk = '1' then
      if rst = '1' then
        c_state <= RESET;
      else
        c_state <= n_state;
      end if;
    end if;
  end process;


end architecture;
